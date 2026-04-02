# -*- coding: utf-8 -*-
"""
深觅 AI Coach - LLM集成服务

本模块提供大语言模型的集成服务，支持：
- LazyLLM框架集成
- OpenAI API调用
- Claude API调用
- 其他兼容OpenAI接口的模型

功能：
- LLM客户端初始化
- 对话生成
- Token用量统计
- 错误处理与重试
"""

import os
import time
import asyncio
from typing import List, Dict, Optional, Any, AsyncGenerator, Union
from dataclasses import dataclass, field
from enum import Enum
import json
import logging

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class LLMProvider(str, Enum):
    """LLM提供商枚举"""
    LAZYLLM = "lazyllm"
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    AZURE_OPENAI = "azure_openai"
    CUSTOM = "custom"


@dataclass
class LLMResponse:
    """LLM响应数据类"""
    content: str
    model: str
    tokens_used: int = 0
    prompt_tokens: int = 0
    completion_tokens: int = 0
    generation_time: float = 0.0
    finish_reason: Optional[str] = None
    _metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class LLMMessage:
    """LLM消息数据类"""
    role: str  # system, user, assistant
    content: str
    name: Optional[str] = None


class LLMConfig:
    """LLM配置类"""
    
    def __init__(
        self,
        provider: LLMProvider = LLMProvider.OPENAI,
        model: str = "gpt-4o-mini",
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 2000,
        top_p: float = 1.0,
        frequency_penalty: float = 0.0,
        presence_penalty: float = 0.0,
        timeout: int = 60,
        max_retries: int = 3,
        retry_delay: float = 1.0,
        **kwargs
    ):
        self.provider = provider
        self.model = model
        self.api_key = api_key or os.getenv("OPENAI_API_KEY", "")
        self.base_url = base_url or os.getenv("OPENAI_BASE_URL", "")
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.top_p = top_p
        self.frequency_penalty = frequency_penalty
        self.presence_penalty = presence_penalty
        self.timeout = timeout
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self.extra_params = kwargs


class LLMService:
    """LLM服务类
    
    提供统一的大语言模型调用接口，支持多种后端
    """
    
    def __init__(self, config: Optional[LLMConfig] = None):
        """初始化LLM服务
        
        Args:
            config: LLM配置，如果为None则使用默认配置
        """
        self.config = config or LLMConfig()
        self._client = None
        self._initialize_client()
    
    def _initialize_client(self):
        """初始化LLM客户端"""
        try:
            if self.config.provider == LLMProvider.LAZYLLM:
                self._init_lazyllm_client()
            elif self.config.provider == LLMProvider.OPENAI:
                self._init_openai_client()
            elif self.config.provider == LLMProvider.ANTHROPIC:
                self._init_anthropic_client()
            elif self.config.provider == LLMProvider.AZURE_OPENAI:
                self._init_azure_openai_client()
            else:
                self._init_openai_client()  # 默认使用OpenAI
        except Exception as e:
            logger.error(f"初始化LLM客户端失败: {e}")
            raise
    
    def _init_lazyllm_client(self):
        """初始化LazyLLM客户端"""
        try:
            import lazyllm
            # LazyLLM OnlineChatModule 初始化
            self._client = lazyllm.OnlineChatModule(
                source="openai",  # 或其他支持的source
                model=self.config.model,
                api_key=self.config.api_key,
                base_url=self.config.base_url
            )
            logger.info(f"LazyLLM客户端初始化成功，模型: {self.config.model}")
        except ImportError:
            logger.warning("LazyLLM未安装，尝试使用OpenAI客户端")
            self._init_openai_client()
    
    def _init_openai_client(self):
        """初始化OpenAI客户端"""
        try:
            from openai import AsyncOpenAI
            self._client = AsyncOpenAI(
                api_key=self.config.api_key,
                base_url=self.config.base_url if self.config.base_url else None,
                timeout=self.config.timeout
            )
            logger.info(f"OpenAI客户端初始化成功，模型: {self.config.model}")
        except ImportError:
            logger.error("OpenAI库未安装，请运行: pip install openai")
            raise
    
    def _init_anthropic_client(self):
        """初始化Anthropic (Claude) 客户端"""
        try:
            from anthropic import AsyncAnthropic
            self._client = AsyncAnthropic(
                api_key=self.config.api_key,
                timeout=self.config.timeout
            )
            logger.info(f"Anthropic客户端初始化成功，模型: {self.config.model}")
        except ImportError:
            logger.error("Anthropic库未安装，请运行: pip install anthropic")
            raise
    
    def _init_azure_openai_client(self):
        """初始化Azure OpenAI客户端"""
        try:
            from openai import AsyncAzureOpenAI
            self._client = AsyncAzureOpenAI(
                api_key=self.config.api_key,
                azure_endpoint=self.config.base_url,
                api_version=self.config.extra_params.get("api_version", "2024-02-01"),
                timeout=self.config.timeout
            )
            logger.info(f"Azure OpenAI客户端初始化成功，模型: {self.config.model}")
        except ImportError:
            logger.error("OpenAI库未安装，请运行: pip install openai")
            raise
    
    async def chat(
        self,
        messages: List[Dict[str, str]],
        system_prompt: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        stream: bool = False
    ) -> Union[LLMResponse, AsyncGenerator[str, None]]:
        """发送对话请求
        
        Args:
            messages: 对话历史消息列表
            system_prompt: 系统提示词
            temperature: 温度参数
            max_tokens: 最大Token数
            stream: 是否流式输出
            
        Returns:
            LLMResponse对象或流式生成器
        """
        start_time = time.time()
        
        # 构建消息列表
        chat_messages = []
        if system_prompt:
            chat_messages.append({"role": "system", "content": system_prompt})
        chat_messages.extend(messages)
        
        # 调用参数
        params = {
            "model": self.config.model,
            "messages": chat_messages,
            "temperature": temperature or self.config.temperature,
            "max_tokens": max_tokens or self.config.max_tokens,
            "top_p": self.config.top_p,
            "frequency_penalty": self.config.frequency_penalty,
            "presence_penalty": self.config.presence_penalty,
            "stream": stream
        }
        
        # 重试机制
        for attempt in range(self.config.max_retries):
            try:
                if stream:
                    return self._stream_chat(params)
                else:
                    return await self._single_chat(params, start_time)
            except Exception as e:
                logger.warning(f"LLM调用失败 (尝试 {attempt + 1}/{self.config.max_retries}): {e}")
                if attempt < self.config.max_retries - 1:
                    await asyncio.sleep(self.config.retry_delay * (attempt + 1))
                else:
                    logger.error(f"LLM调用最终失败: {e}")
                    raise
    
    async def _single_chat(
        self,
        params: Dict[str, Any],
        start_time: float
    ) -> LLMResponse:
        """单次对话调用
        
        Args:
            params: 调用参数
            start_time: 开始时间
            
        Returns:
            LLMResponse对象
        """
        if self.config.provider == LLMProvider.LAZYLLM:
            return await self._call_lazyllm(params, start_time)
        elif self.config.provider == LLMProvider.ANTHROPIC:
            return await self._call_anthropic(params, start_time)
        else:
            return await self._call_openai(params, start_time)
    
    async def _call_openai(
        self,
        params: Dict[str, Any],
        start_time: float
    ) -> LLMResponse:
        """调用OpenAI API
        
        Args:
            params: 调用参数
            start_time: 开始时间
            
        Returns:
            LLMResponse对象
        """
        response = await self._client.chat.completions.create(**params)
        
        generation_time = time.time() - start_time
        
        return LLMResponse(
            content=response.choices[0].message.content,
            model=response.model,
            tokens_used=response.usage.total_tokens if response.usage else 0,
            prompt_tokens=response.usage.prompt_tokens if response.usage else 0,
            completion_tokens=response.usage.completion_tokens if response.usage else 0,
            generation_time=generation_time,
            finish_reason=response.choices[0].finish_reason
        )
    
    async def _call_lazyllm(
        self,
        params: Dict[str, Any],
        start_time: float
    ) -> LLMResponse:
        """调用LazyLLM
        
        Args:
            params: 调用参数
            start_time: 开始时间
            
        Returns:
            LLMResponse对象
        """
        # LazyLLM的调用方式
        # 注意：LazyLLM的具体API可能有所不同，这里做通用处理
        try:
            # 尝试使用LazyLLM的同步调用（包装为异步）
            loop = asyncio.get_event_loop()
            
            # 提取消息内容
            messages = params.get("messages", [])
            prompt = ""
            for msg in messages:
                prompt += f"{msg['role']}: {msg['content']}\n"
            
            # 使用线程池执行同步调用
            result = await loop.run_in_executor(
                None,
                lambda: self._client(prompt)
            )
            
            generation_time = time.time() - start_time
            
            return LLMResponse(
                content=str(result),
                model=self.config.model,
                tokens_used=0,  # LazyLLM可能不提供token统计
                generation_time=generation_time,
                finish_reason="stop"
            )
        except Exception as e:
            logger.error(f"LazyLLM调用失败: {e}")
            # 降级到OpenAI
            return await self._call_openai(params, start_time)
    
    async def _call_anthropic(
        self,
        params: Dict[str, Any],
        start_time: float
    ) -> LLMResponse:
        """调用Anthropic (Claude) API
        
        Args:
            params: 调用参数
            start_time: 开始时间
            
        Returns:
            LLMResponse对象
        """
        # 转换消息格式为Claude格式
        messages = params.get("messages", [])
        system_msg = None
        chat_messages = []
        
        for msg in messages:
            if msg["role"] == "system":
                system_msg = msg["content"]
            else:
                chat_messages.append({
                    "role": msg["role"],
                    "content": msg["content"]
                })
        
        # 构建Claude调用参数
        claude_params = {
            "model": self.config.model,
            "messages": chat_messages,
            "max_tokens": params.get("max_tokens", 2000),
            "temperature": params.get("temperature", 0.7),
        }
        
        if system_msg:
            claude_params["system"] = system_msg
        
        response = await self._client.messages.create(**claude_params)
        
        generation_time = time.time() - start_time
        
        return LLMResponse(
            content=response.content[0].text if response.content else "",
            model=response.model,
            tokens_used=response.usage.input_tokens + response.usage.output_tokens if response.usage else 0,
            prompt_tokens=response.usage.input_tokens if response.usage else 0,
            completion_tokens=response.usage.output_tokens if response.usage else 0,
            generation_time=generation_time,
            finish_reason=response.stop_reason
        )
    
    async def _stream_chat(
        self,
        params: Dict[str, Any]
    ) -> AsyncGenerator[str, None]:
        """流式对话调用
        
        Args:
            params: 调用参数
            
        Yields:
            生成的文本片段
        """
        if self.config.provider == LLMProvider.ANTHROPIC:
            async for chunk in self._stream_anthropic(params):
                yield chunk
        else:
            async for chunk in self._stream_openai(params):
                yield chunk
    
    async def _stream_openai(
        self,
        params: Dict[str, Any]
    ) -> AsyncGenerator[str, None]:
        """OpenAI流式调用
        
        Args:
            params: 调用参数
            
        Yields:
            生成的文本片段
        """
        response = await self._client.chat.completions.create(**params)
        
        async for chunk in response:
            if chunk.choices and chunk.choices[0].delta.content:
                yield chunk.choices[0].delta.content
    
    async def _stream_anthropic(
        self,
        params: Dict[str, Any]
    ) -> AsyncGenerator[str, None]:
        """Anthropic流式调用
        
        Args:
            params: 调用参数
            
        Yields:
            生成的文本片段
        """
        # 转换参数
        messages = params.get("messages", [])
        chat_messages = []
        system_msg = None
        
        for msg in messages:
            if msg["role"] == "system":
                system_msg = msg["content"]
            else:
                chat_messages.append({
                    "role": msg["role"],
                    "content": msg["content"]
                })
        
        claude_params = {
            "model": self.config.model,
            "messages": chat_messages,
            "max_tokens": params.get("max_tokens", 2000),
            "temperature": params.get("temperature", 0.7),
            "stream": True
        }
        
        if system_msg:
            claude_params["system"] = system_msg
        
        async with self._client.messages.stream(**claude_params) as stream:
            async for text in stream.text_stream:
                yield text
    
    async def generate_summary(
        self,
        text: str,
        max_length: int = 200
    ) -> str:
        """生成文本摘要
        
        Args:
            text: 需要摘要的文本
            max_length: 摘要最大长度
            
        Returns:
            摘要文本
        """
        prompt = f"请对以下文本进行摘要，不超过{max_length}字：\n\n{text}"
        
        messages = [{"role": "user", "content": prompt}]
        response = await self.chat(messages, max_tokens=max_length * 2)
        
        return response.content
    
    async def analyze_sentiment(
        self,
        text: str
    ) -> Dict[str, Any]:
        """分析文本情感
        
        Args:
            text: 需要分析的文本
            
        Returns:
            情感分析结果
        """
        prompt = f"""请分析以下文本的情感，以JSON格式返回：

文本：{text}

请返回以下格式的JSON：
{{
    "emotion": "主要情感（positive/negative/anxious/confused/frustrated/excited/grateful/sad/neutral）",
    "intensity": 情感强度（1-10）,
    "keywords": ["关键词1", "关键词2"],
    "explanation": "简要解释"
}}
"""
        
        messages = [{"role": "user", "content": prompt}]
        response = await self.chat(messages, temperature=0.3, max_tokens=500)
        
        try:
            # 尝试解析JSON响应
            content = response.content
            # 提取JSON部分
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0]
            elif "```" in content:
                content = content.split("```")[1].split("```")[0]
            
            result = json.loads(content.strip())
            return result
        except json.JSONDecodeError:
            logger.warning(f"情感分析JSON解析失败: {response.content}")
            return {
                "emotion": "neutral",
                "intensity": 5,
                "keywords": [],
                "explanation": "解析失败"
            }
    
    def get_usage_stats(self) -> Dict[str, Any]:
        """获取使用统计
        
        Returns:
            使用统计信息
        """
        return {
            "provider": self.config.provider.value,
            "model": self.config.model,
            "config": {
                "temperature": self.config.temperature,
                "max_tokens": self.config.max_tokens
            }
        }


# =============================================================================
# 便捷函数和全局实例
# =============================================================================

# 全局LLM服务实例
_llm_service: Optional[LLMService] = None


def get_llm_service() -> LLMService:
    """获取全局LLM服务实例
    
    Returns:
        LLMService实例
    """
    global _llm_service
    if _llm_service is None:
        _llm_service = LLMService()
    return _llm_service


def init_llm_service(config: LLMConfig) -> LLMService:
    """初始化LLM服务
    
    Args:
        config: LLM配置
        
    Returns:
        LLMService实例
    """
    global _llm_service
    _llm_service = LLMService(config)
    return _llm_service


async def quick_chat(
    message: str,
    system_prompt: Optional[str] = None,
    **kwargs
) -> str:
    """快速对话函数
    
    Args:
        message: 用户消息
        system_prompt: 系统提示词
        **kwargs: 其他参数
        
    Returns:
        AI回复内容
    """
    service = get_llm_service()
    messages = [{"role": "user", "content": message}]
    response = await service.chat(messages, system_prompt=system_prompt, **kwargs)
    return response.content


# 配置示例
DEFAULT_CONFIGS = {
    "openai_gpt4": LLMConfig(
        provider=LLMProvider.OPENAI,
        model="gpt-4o",
        temperature=0.7,
        max_tokens=2000
    ),
    "openai_gpt4_mini": LLMConfig(
        provider=LLMProvider.OPENAI,
        model="gpt-4o-mini",
        temperature=0.7,
        max_tokens=2000
    ),
    "claude_sonnet": LLMConfig(
        provider=LLMProvider.ANTHROPIC,
        model="claude-3-sonnet-20240229",
        temperature=0.7,
        max_tokens=2000
    ),
    "claude_haiku": LLMConfig(
        provider=LLMProvider.ANTHROPIC,
        model="claude-3-haiku-20240307",
        temperature=0.7,
        max_tokens=2000
    ),
}
