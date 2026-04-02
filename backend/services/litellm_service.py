# -*- coding: utf-8 -*-
"""
深觅 AI Coach - LiteLLM路由服务 (v2)

基于LiteLLM的统一大语言模型路由服务：
- 支持多模型统一接口
- 自动回退策略
- 结构化输出(JSON模式)
- 成本控制和监控
- 异步流式响应

配置文件: config/llm_config.yaml
"""

import os
import yaml
import json
import time
import asyncio
from typing import List, Dict, Optional, Any, AsyncGenerator, Union, Type
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
import logging

# LiteLLM导入
try:
    import litellm
    from litellm import acompletion, completion
    from litellm.utils import ModelResponse
    LITELLM_AVAILABLE = True
except ImportError:
    LITELLM_AVAILABLE = False
    logging.warning("LiteLLM未安装，使用降级方案。运行: pip install litellm")

# Pydantic用于结构化输出
from pydantic import BaseModel, Field, ValidationError

# 配置日志
logger = logging.getLogger(__name__)


# =============================================================================
# 数据模型
# =============================================================================

class ResponseFormat(str, Enum):
    """响应格式枚举"""
    TEXT = "text"
    JSON = "json"
    JSON_SCHEMA = "json_schema"


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
    structured_data: Optional[Dict[str, Any]] = None  # 结构化输出数据
    _metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class LLMMessage:
    """LLM消息数据类"""
    role: str  # system, user, assistant
    content: str
    name: Optional[str] = None


class CoachIntent(BaseModel):
    """教练意图识别 - 结构化输出模型"""
    intent_type: str = Field(..., description="意图类型: explore_strength, goal_setting, problem_solving, emotional_support, action_planning, reflection")
    confidence: float = Field(..., ge=0, le=1, description="置信度 0-1")
    key_topics: List[str] = Field(default_factory=list, description="关键话题")
    user_emotion: str = Field(default="neutral", description="用户情绪: positive, negative, anxious, confused, frustrated, excited, grateful, sad, neutral")
    suggested_approach: str = Field(..., description="建议的教练方法")


class UserInsight(BaseModel):
    """用户洞察提取 - 结构化输出模型"""
    strengths_mentioned: List[str] = Field(default_factory=list, description="提到的优势")
    challenges: List[str] = Field(default_factory=list, description="面临的挑战")
    goals: List[str] = Field(default_factory=list, description="目标")
    values: List[str] = Field(default_factory=list, description="价值观")
    patterns: List[str] = Field(default_factory=list, description="行为模式")
    action_items: List[str] = Field(default_factory=list, description="行动项")


class SessionSummary(BaseModel):
    """会话摘要 - 结构化输出模型"""
    key_insights: List[str] = Field(..., description="关键洞察")
    progress_made: str = Field(..., description="取得的进展")
    next_steps: List[str] = Field(..., description="下一步行动")
    strengths_highlighted: List[str] = Field(default_factory=list, description="强调的优势")
    coach_techniques_used: List[str] = Field(default_factory=list, description="使用的教练技术")


# =============================================================================
# 配置管理
# =============================================================================

class LiteLLMConfig:
    """LiteLLM配置管理"""
    
    DEFAULT_CONFIG_PATH = Path(__file__).parent.parent / "config" / "llm_config.yaml"
    
    def __init__(self, config_path: Optional[str] = None):
        self.config_path = Path(config_path) if config_path else self.DEFAULT_CONFIG_PATH
        self.config = self._load_config()
        
    def _load_config(self) -> Dict[str, Any]:
        """加载配置文件"""
        if not self.config_path.exists():
            logger.warning(f"配置文件不存在: {self.config_path}，使用默认配置")
            return self._default_config()
        
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)
            logger.info(f"加载配置文件: {self.config_path}")
            return config
        except Exception as e:
            logger.error(f"加载配置文件失败: {e}")
            return self._default_config()
    
    def _default_config(self) -> Dict[str, Any]:
        """默认配置"""
        return {
            "model_list": [
                {
                    "model_name": "kimi-k2-turbo-preview",
                    "litellm_params": {
                        "model": "openai/kimi-k2-turbo-preview",
                        "api_base": "https://api.moonshot.cn/v1",
                        "api_key": os.getenv("KIMI_API_KEY", ""),  # 项目统一环境变量
                        "temperature": 0.7,
                        "max_tokens": 4000
                    }
                },
                {
                    "model_name": "moonshot-v1-8k",
                    "litellm_params": {
                        "model": "openai/moonshot-v1-8k",
                        "api_base": "https://api.moonshot.cn/v1",
                        "api_key": os.getenv("KIMI_API_KEY", ""),
                        "temperature": 0.7,
                        "max_tokens": 4000
                    }
                },
                {
                    "model_name": "kimi-k2.5",
                    "litellm_params": {
                        "model": "openai/kimi-k2.5",
                        "api_base": "https://api.moonshot.cn/v1",
                        "api_key": os.getenv("KIMI_API_KEY", ""),
                        "temperature": 1.0,
                        "max_tokens": 4000
                    }
                }
            ],
            "model_alias": {
                "coach-chat": "kimi-k2-turbo-preview",
                "coach-chat-fallback": "moonshot-v1-8k",
                "structured-output": "kimi-k2-turbo-preview",
                "deep-analysis": "kimi-k2.5",
                "default": "kimi-k2-turbo-preview"
            },
            "router_settings": {
                "timeout": 60,
                "num_retries": 2,
                "retry_after": 1,
                "fallback_strategy": [
                    {"model": "kimi-k2.5", "fallback": ["kimi-k2-turbo-preview", "moonshot-v1-8k"]},
                    {"model": "kimi-k2-turbo-preview", "fallback": ["moonshot-v1-8k"]}
                ]
            }
        }
    
    def get_model_config(self, model_name: str) -> Optional[Dict[str, Any]]:
        """获取模型配置（支持别名解析）"""
        # 先检查是否是别名
        aliases = self.config.get("model_alias", {})
        if model_name in aliases:
            model_name = aliases[model_name]
        
        # 查找模型配置
        for model in self.config.get("model_list", []):
            if model["model_name"] == model_name:
                return model
        return None
    
    def resolve_model_alias(self, alias: str) -> str:
        """解析模型别名"""
        aliases = self.config.get("model_alias", {})
        return aliases.get(alias, alias)
    
    def get_fallback_list(self, model_name: str) -> List[str]:
        """获取回退列表（支持新的回退策略配置）"""
        # 先解析别名
        model_name = self.resolve_model_alias(model_name)
        
        # 查找回退策略
        router_settings = self.config.get("router_settings", {})
        fallback_strategy = router_settings.get("fallback_strategy", [])
        
        for strategy in fallback_strategy:
            if strategy.get("model") == model_name:
                return strategy.get("fallback", [])
        
        # 默认回退到轻量级模型
        if model_name == "kimi-k2.5":
            return ["kimi-k2-turbo-preview", "moonshot-v1-8k"]
        elif model_name == "kimi-k2-turbo-preview":
            return ["moonshot-v1-8k"]
        
        return []
    
    def get_routing_strategy(self, strategy_name: str) -> Dict[str, Any]:
        """获取路由策略"""
        strategies = self.config.get("routing_strategy", {})
        return strategies.get(strategy_name, strategies.get("short_context", {}))


# =============================================================================
# LiteLLM服务
# =============================================================================

class LiteLLMService:
    """LiteLLM路由服务
    
    提供统一的多模型LLM调用接口，支持：
    - 多模型路由
    - 自动回退
    - 结构化输出
    - 流式响应
    """
    
    def __init__(self, config: Optional[LiteLLMConfig] = None):
        """初始化服务
        
        Args:
            config: 配置对象，如果为None则使用默认配置
        """
        if not LITELLM_AVAILABLE:
            raise ImportError("LiteLLM未安装，请运行: pip install litellm")
        
        self.config = config or LiteLLMConfig()
        self._setup_litellm()
        
    def _setup_litellm(self):
        """配置LiteLLM"""
        # 设置日志级别
        litellm.set_verbose = False
        
        # 配置重试和超时
        router_settings = self.config.config.get("router_settings", {})
        litellm.request_timeout = router_settings.get("timeout", 30)
        litellm.num_retries = router_settings.get("num_retries", 2)
        
        logger.info("LiteLLM服务初始化完成")
    
    async def chat(
        self,
        messages: List[Dict[str, str]],
        model: Optional[str] = None,
        system_prompt: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        stream: bool = False,
        response_format: Optional[ResponseFormat] = None,
        json_schema: Optional[Type[BaseModel]] = None,
        fallback_models: Optional[List[str]] = None
    ) -> Union[LLMResponse, AsyncGenerator[str, None]]:
        """发送对话请求
        
        Args:
            messages: 对话历史消息列表
            model: 模型名称，默认使用配置中的主模型
            system_prompt: 系统提示词
            temperature: 温度参数
            max_tokens: 最大Token数
            stream: 是否流式输出
            response_format: 响应格式
            json_schema: JSON Schema模型（用于结构化输出）
            fallback_models: 自定义回退模型列表
            
        Returns:
            LLMResponse对象或流式生成器
        """
        start_time = time.time()
        
        # 确定模型（支持别名）
        model_name = model or "default"
        model_name = self.config.resolve_model_alias(model_name)
        model_config = self.config.get_model_config(model_name)
        
        if not model_config:
            logger.warning(f"模型配置未找到: {model_name}，使用默认")
            model_name = "kimi-k2-turbo-preview"
            model_config = self.config.get_model_config(model_name)
        
        # 构建消息列表
        chat_messages = []
        if system_prompt:
            chat_messages.append({"role": "system", "content": system_prompt})
        chat_messages.extend(messages)
        
        # 构建调用参数
        litellm_params = model_config.get("litellm_params", {}).copy()
        
        # 覆盖参数
        if temperature is not None:
            litellm_params["temperature"] = temperature
        if max_tokens is not None:
            litellm_params["max_tokens"] = max_tokens
            
        # 处理结构化输出
        if response_format == ResponseFormat.JSON_SCHEMA and json_schema:
            litellm_params["response_format"] = {"type": "json_object"}
            # 添加schema说明到system prompt
            schema_desc = self._schema_to_prompt(json_schema)
            if chat_messages and chat_messages[0]["role"] == "system":
                chat_messages[0]["content"] += f"\n\n{schema_desc}"
            else:
                chat_messages.insert(0, {"role": "system", "content": schema_desc})
        
        # 获取回退列表（支持新的回退策略）
        fallback_list = fallback_models or self.config.get_fallback_list(model_name)
        
        # 尝试调用（带自动回退）
        last_error = None
        for attempt_model in [model_name] + [m for m in fallback_list if m != model_name]:
            try:
                model_params = self._get_model_params(attempt_model, litellm_params)
                
                if stream:
                    return self._stream_chat(chat_messages, model_params)
                else:
                    response = await self._single_chat(chat_messages, model_params)
                    
                    # 如果请求结构化输出，解析JSON
                    if response_format in [ResponseFormat.JSON, ResponseFormat.JSON_SCHEMA]:
                        response = self._parse_structured_response(response, json_schema)
                    
                    response.generation_time = time.time() - start_time
                    return response
                    
            except Exception as e:
                logger.warning(f"模型 {attempt_model} 调用失败: {e}")
                last_error = e
                continue
        
        # 所有模型都失败
        logger.error(f"所有模型调用失败，最后错误: {last_error}")
        raise last_error or Exception("所有模型调用失败")
    
    def _get_model_params(self, model_name: str, base_params: Dict[str, Any]) -> Dict[str, Any]:
        """获取模型调用参数"""
        model_config = self.config.get_model_config(model_name)
        if not model_config:
            return {**base_params, "model": model_name}
        
        params = model_config.get("litellm_params", {}).copy()
        params.update({k: v for k, v in base_params.items() if v is not None})
        return params
    
    async def _single_chat(
        self,
        messages: List[Dict[str, str]],
        params: Dict[str, Any]
    ) -> LLMResponse:
        """单次对话调用"""
        response = await acompletion(
            messages=messages,
            **params
        )
        
        # 解析响应
        content = response.choices[0].message.content or ""
        model_used = response.model or params.get("model", "unknown")
        
        # 获取token使用量
        usage = response.usage
        tokens_used = usage.total_tokens if usage else 0
        prompt_tokens = usage.prompt_tokens if usage else 0
        completion_tokens = usage.completion_tokens if usage else 0
        
        return LLMResponse(
            content=content,
            model=model_used,
            tokens_used=tokens_used,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            finish_reason=response.choices[0].finish_reason
        )
    
    async def _stream_chat(
        self,
        messages: List[Dict[str, str]],
        params: Dict[str, Any]
    ) -> AsyncGenerator[str, None]:
        """流式对话调用"""
        params["stream"] = True
        
        response = await acompletion(
            messages=messages,
            **params
        )
        
        async for chunk in response:
            if chunk.choices and chunk.choices[0].delta.content:
                yield chunk.choices[0].delta.content
    
    def _parse_structured_response(
        self,
        response: LLMResponse,
        schema: Optional[Type[BaseModel]] = None
    ) -> LLMResponse:
        """解析结构化响应"""
        try:
            content = response.content.strip()
            
            # 提取JSON部分
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0]
            elif "```" in content:
                content = content.split("```")[1].split("```")[0]
            
            data = json.loads(content.strip())
            response.structured_data = data
            
            # 如果提供了schema，验证数据
            if schema:
                validated = schema(**data)
                response.structured_data = validated.model_dump()
                
        except (json.JSONDecodeError, ValidationError) as e:
            logger.warning(f"结构化解析失败: {e}")
            response.structured_data = {"raw_content": response.content}
        
        return response
    
    def _schema_to_prompt(self, schema: Type[BaseModel]) -> str:
        """将Pydantic schema转换为prompt说明"""
        schema_dict = schema.model_json_schema()
        
        prompt = "你必须以JSON格式返回结果，格式如下:\n\n"
        prompt += json.dumps(schema_dict.get("properties", {}), indent=2, ensure_ascii=False)
        prompt += "\n\n确保返回的是有效的JSON，不要添加markdown格式或其他说明。"
        
        return prompt
    
    # =============================================================================
    # 结构化信息提取方法
    # =============================================================================
    
    async def extract_intent(
        self,
        user_message: str,
        conversation_history: Optional[List[Dict[str, str]]] = None
    ) -> CoachIntent:
        """提取用户意图
        
        Args:
            user_message: 用户消息
            conversation_history: 对话历史
            
        Returns:
            CoachIntent对象
        """
        system_prompt = """你是一位专业的AI教练意图分析专家。请分析用户消息，识别其意图类型、情绪和关键话题。

意图类型包括:
- explore_strength: 探索优势
- goal_setting: 目标设定
- problem_solving: 问题解决
- emotional_support: 情绪支持
- action_planning: 行动计划
- reflection: 反思总结

请以JSON格式返回结果。"""

        messages = []
        if conversation_history:
            messages.extend(conversation_history[-3:])  # 只取最近3条
        messages.append({"role": "user", "content": user_message})
        
        response = await self.chat(
            messages=messages,
            system_prompt=system_prompt,
            model="structured-output",  # 使用结构化输出专用模型
            temperature=0.3,
            max_tokens=500,
            response_format=ResponseFormat.JSON_SCHEMA,
            json_schema=CoachIntent
        )
        
        if response.structured_data:
            return CoachIntent(**response.structured_data)
        
        # 回退到默认
        return CoachIntent(
            intent_type="explore_strength",
            confidence=0.5,
            key_topics=[],
            user_emotion="neutral",
            suggested_approach="使用开放式提问探索用户想法"
        )
    
    async def extract_insights(
        self,
        conversation_text: str
    ) -> UserInsight:
        """从对话中提取用户洞察
        
        Args:
            conversation_text: 对话文本
            
        Returns:
            UserInsight对象
        """
        system_prompt = """你是一位专业的教练对话分析师。请仔细阅读以下对话，提取关键信息：
- 用户提到的优势
- 面临的挑战
- 目标
- 价值观
- 行为模式
- 行动项

请以JSON格式返回结果。"""

        response = await self.chat(
            messages=[{"role": "user", "content": conversation_text[:4000]}],
            system_prompt=system_prompt,
            model="structured-output",  # 使用结构化输出专用模型
            temperature=0.3,
            max_tokens=1000,
            response_format=ResponseFormat.JSON_SCHEMA,
            json_schema=UserInsight
        )
        
        if response.structured_data:
            return UserInsight(**response.structured_data)
        
        return UserInsight()
    
    async def generate_session_summary(
        self,
        messages: List[Dict[str, str]],
        user_profile: Optional[Dict[str, Any]] = None
    ) -> SessionSummary:
        """生成会话摘要
        
        Args:
            messages: 对话消息列表
            user_profile: 用户画像
            
        Returns:
            SessionSummary对象
        """
        # 构建对话文本
        conversation_text = "\n".join([
            f"{m['role']}: {m['content']}"
            for m in messages[-20:]  # 只取最近20条
        ])
        
        system_prompt = """你是一位专业的教练会话总结专家。请根据对话内容生成结构化摘要。

请包含:
1. 关键洞察 (3-5条)
2. 取得的进展
3. 下一步行动建议 (2-3条)
4. 强调的优势
5. 使用的教练技术

请以JSON格式返回结果。"""

        user_prompt = f"""对话内容:\n{conversation_text}\n\n"""
        if user_profile:
            user_prompt += f"用户画像: {json.dumps(user_profile, ensure_ascii=False)}\n"
        
        response = await self.chat(
            messages=[{"role": "user", "content": user_prompt}],
            system_prompt=system_prompt,
            model="session-summary",  # 使用会话摘要专用模型
            temperature=0.4,
            max_tokens=800,
            response_format=ResponseFormat.JSON_SCHEMA,
            json_schema=SessionSummary
        )
        
        if response.structured_data:
            return SessionSummary(**response.structured_data)
        
        return SessionSummary(
            key_insights=["对话进行中"],
            progress_made="持续探索中",
            next_steps=["继续对话"]
        )
    
    async def generate_coach_response(
        self,
        user_message: str,
        conversation_history: List[Dict[str, str]],
        user_profile: Optional[Dict[str, Any]] = None,
        strength_profile: Optional[Dict[str, Any]] = None,
        emotion_context: Optional[Dict[str, Any]] = None
    ) -> str:
        """生成教练回复
        
        Args:
            user_message: 用户消息
            conversation_history: 对话历史
            user_profile: 用户画像
            strength_profile: 优势档案
            emotion_context: 情感上下文
            
        Returns:
            教练回复文本
        """
        # 构建系统提示词
        system_prompt = self._build_coach_system_prompt(
            user_profile, strength_profile, emotion_context
        )
        
        # 构建消息列表
        messages = conversation_history[-10:]  # 最近10条
        messages.append({"role": "user", "content": user_message})
        
        # 先提取意图
        intent = await self.extract_intent(user_message, conversation_history)
        
        # 根据意图调整提示词
        if intent.intent_type == "emotional_support":
            system_prompt += "\n\n用户当前需要情绪支持，请先共情，再引导。"
        elif intent.intent_type == "goal_setting":
            system_prompt += "\n\n用户在进行目标设定，使用GROW模型帮助澄清目标。"
        elif intent.intent_type == "action_planning":
            system_prompt += "\n\n用户在制定行动计划，帮助其制定具体可行的步骤。"
        
        response = await self.chat(
            messages=messages,
            system_prompt=system_prompt,
            model="coach-chat",  # 使用模型别名
            temperature=0.7,
            max_tokens=2000
        )
        
        return response.content
    
    def _build_coach_system_prompt(
        self,
        user_profile: Optional[Dict[str, Any]] = None,
        strength_profile: Optional[Dict[str, Any]] = None,
        emotion_context: Optional[Dict[str, Any]] = None
    ) -> str:
        """构建教练系统提示词"""
        prompt_parts = [
            "你是一位专业的优势教练，名叫'深寻'。你的任务是帮助用户发现和发挥个人优势。",
            "",
            "核心原则:",
            "1. 提问而非告知 - 使用开放式问题引导用户思考",
            "2. 聚焦优势 - 帮助用户识别和运用个人优势",
            "3. 共创关系 - 与用户建立平等的伙伴关系",
            "4. 行动导向 - 支持用户制定具体行动计划",
            "",
            "沟通风格:",
            "- 温暖、支持性但专业的语气",
            "- 适度使用emoji增加亲和力",
            "- 回应简洁但有深度，避免冗长",
            "- 在适当时机使用教练工具（如GROW模型、力量提问）"
        ]
        
        # 添加用户画像
        if user_profile:
            nickname = user_profile.get("nickname", "")
            if nickname:
                prompt_parts.append(f"\n用户昵称: {nickname}")
        
        # 添加优势档案
        if strength_profile:
            top_strengths = strength_profile.get("top_strengths", [])
            if top_strengths:
                strength_names = [s.get("name", "") for s in top_strengths[:3]]
                prompt_parts.append(f"\n用户Top3优势: {', '.join(strength_names)}")
                prompt_parts.append("在对话中可以适当提及这些优势，帮助用户更好地运用它们。")
        
        # 添加情感上下文
        if emotion_context:
            emotion = emotion_context.get("emotion", "")
            intensity = emotion_context.get("intensity", 5)
            if emotion and emotion != "neutral":
                prompt_parts.append(f"\n注意: 用户当前情绪为{emotion}（强度{intensity}/10），请适当回应。")
        
        return "\n".join(prompt_parts)


# =============================================================================
# 便捷函数和全局实例
# =============================================================================

_llm_service: Optional[LiteLLMService] = None


def get_litellm_service() -> LiteLLMService:
    """获取全局LiteLLM服务实例
    
    Returns:
        LiteLLMService实例
    """
    global _llm_service
    if _llm_service is None:
        _llm_service = LiteLLMService()
    return _llm_service


def init_litellm_service(config_path: Optional[str] = None) -> LiteLLMService:
    """初始化LiteLLM服务
    
    Args:
        config_path: 配置文件路径
        
    Returns:
        LiteLLMService实例
    """
    global _llm_service
    config = LiteLLMConfig(config_path)
    _llm_service = LiteLLMService(config)
    return _llm_service


# 兼容性: 保持与旧版LLMService相同的接口
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
    service = get_litellm_service()
    messages = [{"role": "user", "content": message}]
    response = await service.chat(messages, system_prompt=system_prompt, **kwargs)
    return response.content
