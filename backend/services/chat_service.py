# -*- coding: utf-8 -*-
"""
深觅 AI Coach - 对话服务核心

本模块提供对话管理的核心功能：
- 创建新对话
- 发送消息并获取AI回复
- 维护对话历史
- 生成对话摘要
- 情感分析集成
- 对话配额管理

对话流程：
用户发送消息 → 情感分析 → 构建Prompt（历史+用户画像）→ LLM生成 → 保存消息 → 返回回复
"""

import uuid
import json
import asyncio
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Any, Tuple
from dataclasses import dataclass, field
from enum import Enum
import logging

# 配置日志
logger = logging.getLogger(__name__)


class ConversationStatus(str, Enum):
    """对话状态枚举"""
    ACTIVE = "active"                    # 活跃
    ARCHIVED = "archived"                # 已归档
    DELETED = "deleted"                  # 已删除


class MessageRole(str, Enum):
    """消息角色枚举"""
    USER = "user"                        # 用户
    ASSISTANT = "assistant"              # AI助手
    SYSTEM = "system"                    # 系统
    COACH = "coach"                      # 教练


@dataclass
class Message:
    """消息数据类"""
    id: str
    conversation_id: str
    role: MessageRole
    content: str
    emotion_tag: Optional[str] = None
    sentiment_score: Optional[float] = None
    tokens_used: int = 0
    response_time_ms: int = 0
    model: Optional[str] = None
    _metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.utcnow)
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "id": self.id,
            "conversation_id": self.conversation_id,
            "role": self.role.value,
            "content": self.content,
            "emotion_tag": self.emotion_tag,
            "sentiment_score": self.sentiment_score,
            "tokens_used": self.tokens_used,
            "response_time_ms": self.response_time_ms,
            "model": self.model,
            "_metadata": self._metadata,
            "created_at": self.created_at.isoformat()
        }


@dataclass
class Conversation:
    """对话数据类"""
    id: str
    user_id: str
    title: str
    status: ConversationStatus
    coach_type: str
    context: Dict[str, Any]
    message_count: int
    created_at: datetime
    updated_at: datetime
    last_message_at: Optional[datetime] = None
    _metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "id": self.id,
            "user_id": self.user_id,
            "title": self.title,
            "status": self.status.value,
            "coach_type": self.coach_type,
            "context": self.context,
            "message_count": self.message_count,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "last_message_at": self.last_message_at.isoformat() if self.last_message_at else None,
            "_metadata": self._metadata
        }


@dataclass
class ChatResponse:
    """聊天响应数据类"""
    message_id: str
    conversation_id: str
    user_message: Message
    ai_message: Message
    emotion_analysis: Optional[Dict[str, Any]] = None


# =============================================================================
# 模拟数据存储（实际项目中应使用数据库）
# =============================================================================

class ConversationStore:
    """对话存储（模拟数据库）
    
    实际项目中应替换为真实的数据库操作
    """
    
    def __init__(self):
        self._conversations: Dict[str, Conversation] = {}
        self._messages: Dict[str, List[Message]] = {}
        self._user_conversations: Dict[str, List[str]] = {}
    
    # 对话操作
    async def create_conversation(self, conversation: Conversation) -> Conversation:
        """创建对话"""
        self._conversations[conversation.id] = conversation
        self._messages[conversation.id] = []
        
        if conversation.user_id not in self._user_conversations:
            self._user_conversations[conversation.user_id] = []
        self._user_conversations[conversation.user_id].append(conversation.id)
        
        return conversation
    
    async def get_conversation(self, conversation_id: str) -> Optional[Conversation]:
        """获取对话"""
        return self._conversations.get(conversation_id)
    
    async def update_conversation(self, conversation: Conversation) -> Conversation:
        """更新对话"""
        self._conversations[conversation.id] = conversation
        return conversation
    
    async def delete_conversation(self, conversation_id: str) -> bool:
        """删除对话"""
        if conversation_id in self._conversations:
            conversation = self._conversations[conversation_id]
            del self._conversations[conversation_id]
            del self._messages[conversation_id]
            
            if conversation.user_id in self._user_conversations:
                self._user_conversations[conversation.user_id].remove(conversation_id)
            
            return True
        return False
    
    async def list_user_conversations(
        self,
        user_id: str,
        limit: int = 20,
        offset: int = 0
    ) -> List[Conversation]:
        """获取用户对话列表"""
        conversation_ids = self._user_conversations.get(user_id, [])
        conversations = [
            self._conversations[cid]
            for cid in conversation_ids
            if cid in self._conversations
        ]
        # 按更新时间排序
        conversations.sort(key=lambda c: c.updated_at, reverse=True)
        return conversations[offset:offset + limit]
    
    # 消息操作
    async def add_message(self, message: Message) -> Message:
        """添加消息"""
        if message.conversation_id not in self._messages:
            self._messages[message.conversation_id] = []
        self._messages[message.conversation_id].append(message)
        return message
    
    async def get_messages(
        self,
        conversation_id: str,
        limit: int = 100,
        offset: int = 0
    ) -> List[Message]:
        """获取消息列表"""
        messages = self._messages.get(conversation_id, [])
        # 按时间排序
        messages.sort(key=lambda m: m.created_at)
        return messages[offset:offset + limit]
    
    async def get_message_count(self, conversation_id: str) -> int:
        """获取消息数量"""
        return len(self._messages.get(conversation_id, []))


# 全局存储实例
_conversation_store: Optional[ConversationStore] = None


def get_conversation_store() -> ConversationStore:
    """获取对话存储实例"""
    global _conversation_store
    if _conversation_store is None:
        _conversation_store = ConversationStore()
    return _conversation_store


# =============================================================================
# 对话服务
# =============================================================================

class ChatService:
    """对话服务类
    
    提供对话管理的核心功能
    """
    
    def __init__(
        self,
        llm_service=None,
        emotion_analyzer=None,
        conversation_store=None,
        memory_service=None
    ):
        """初始化对话服务
        
        Args:
            llm_service: LLM服务实例
            emotion_analyzer: 情感分析器实例
            conversation_store: 对话存储实例
            memory_service: 记忆服务实例
        """
        self._llm_service = llm_service
        self._emotion_analyzer = emotion_analyzer
        self._store = conversation_store or get_conversation_store()
        self._memory_service = memory_service
        
        # 延迟初始化
        if self._llm_service is None:
            try:
                # 优先使用新的 LiteLLM 服务
                from services.litellm_service import get_litellm_service
                self._llm_service = get_litellm_service()
                logger.info("使用 LiteLLM 服务")
            except Exception as e:
                logger.warning(f"LiteLLM 服务初始化失败，回退到旧版: {e}")
                try:
                    from services.llm_service import get_llm_service
                    self._llm_service = get_llm_service()
                    logger.info("使用旧版 LLM 服务")
                except Exception as e2:
                    logger.error(f"所有 LLM 服务初始化失败: {e2}")
        
        if self._emotion_analyzer is None:
            try:
                from services.emotion_analyzer import get_emotion_analyzer
                self._emotion_analyzer = get_emotion_analyzer(use_llm=False)
            except Exception as e:
                logger.warning(f"情感分析器初始化失败: {e}")
        
        # 初始化记忆服务
        if self._memory_service is None:
            try:
                from services.memory_service import MemoryService
                self._memory_service = MemoryService()
                logger.info("记忆服务初始化成功")
            except Exception as e:
                logger.warning(f"记忆服务初始化失败: {e}")
    
    async def create_conversation(
        self,
        user_id: str,
        title: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None,
        coach_type: str = "strength"
    ) -> Conversation:
        """创建新对话
        
        Args:
            user_id: 用户ID
            title: 对话标题
            context: 对话上下文
            coach_type: 教练类型
            
        Returns:
            创建的对话对象
        """
        now = datetime.utcnow()
        conversation = Conversation(
            id=f"conv_{uuid.uuid4().hex[:16]}",
            user_id=user_id,
            title=title or "新对话",
            status=ConversationStatus.ACTIVE,
            coach_type=coach_type,
            context=context or {},
            message_count=0,
            created_at=now,
            updated_at=now,
            last_message_at=None
        )
        
        await self._store.create_conversation(conversation)
        logger.info(f"创建对话: {conversation.id}, 用户: {user_id}")
        
        # 如果是第一次对话，发送欢迎消息
        if context and context.get("is_first_conversation", False):
            await self._send_welcome_message(conversation)
        
        return conversation
    
    async def _send_welcome_message(self, conversation: Conversation):
        """发送欢迎消息
        
        Args:
            conversation: 对话对象
        """
        # 构建欢迎消息
        welcome_content = self._generate_welcome_message(conversation)
        
        welcome_message = Message(
            id=f"msg_{uuid.uuid4().hex[:16]}",
            conversation_id=conversation.id,
            role=MessageRole.ASSISTANT,
            content=welcome_content,
            created_at=datetime.utcnow()
        )
        
        await self._store.add_message(welcome_message)
        
        # 更新对话
        conversation.message_count = 1
        conversation.last_message_at = datetime.utcnow()
        await self._store.update_conversation(conversation)
    
    def _generate_welcome_message(self, conversation: Conversation) -> str:
        """生成欢迎消息
        
        Args:
            conversation: 对话对象
            
        Returns:
            欢迎消息内容
        """
        # 获取用户画像和优势档案
        user_profile = conversation.context.get("user_profile", {})
        strength_profile = conversation.context.get("strength_profile", {})
        
        nickname = user_profile.get("nickname", "")
        top_strengths = strength_profile.get("top_strengths", [])
        
        # 构建个性化欢迎消息
        welcome_parts = []
        
        # 问候
        if nickname:
            welcome_parts.append(f"你好，{nickname}！我是深寻，你的AI优势教练。😊")
        else:
            welcome_parts.append("你好！我是深寻，你的AI优势教练。😊")
        
        # 自我介绍
        welcome_parts.append(
            "我在这里帮助你发现和发挥你的内在优势，无论你想要探索职业发展、人际关系，还是个人成长，"
            "我都会陪伴你一起发现属于你的独特力量。"
        )
        
        # 如果有优势档案，提及优势
        if top_strengths:
            strength_names = [s.get("name", "") for s in top_strengths[:3]]
            if strength_names:
                welcome_parts.append(
                    f"从你的测评结果来看，你的前三大优势是：{', '.join(strength_names)}。"
                    "我们可以从这些优势出发，探索如何更好地发挥它们。"
                )
        
        # 开场邀请
        welcome_parts.append("今天，你希望聊些什么呢？")
        
        return "\n\n".join(welcome_parts)
    
    async def send_message(
        self,
        conversation_id: str,
        content: str,
        user_id: Optional[str] = None
    ) -> ChatResponse:
        """发送消息并获取AI回复
        
        Args:
            conversation_id: 对话ID
            content: 消息内容
            user_id: 用户ID（用于验证）
            
        Returns:
            聊天响应
        """
        start_time = datetime.utcnow()
        
        # 获取对话
        conversation = await self._store.get_conversation(conversation_id)
        if not conversation:
            raise ValueError(f"对话不存在: {conversation_id}")
        
        # 验证用户权限
        if user_id and conversation.user_id != user_id:
            raise PermissionError("无权访问此对话")
        
        # 检查对话状态
        if conversation.status != ConversationStatus.ACTIVE:
            raise ValueError("对话已结束或已删除")
        
        # 1. 情感分析
        emotion_result = None
        if self._emotion_analyzer:
            try:
                emotion_result = await self._emotion_analyzer.analyze(content)
                logger.debug(f"情感分析结果: {emotion_result.emotion.value}, 强度: {emotion_result.intensity}")
            except Exception as e:
                logger.warning(f"情感分析失败: {e}")
        
        # 2. 保存用户消息
        user_message = Message(
            id=f"msg_{uuid.uuid4().hex[:16]}",
            conversation_id=conversation_id,
            role=MessageRole.USER,
            content=content,
            emotion_tag=emotion_result.emotion.value if emotion_result else None,
            sentiment_score=emotion_result.intensity / 10 if emotion_result else None,
            created_at=datetime.utcnow()
        )
        await self._store.add_message(user_message)
        
        # 2.5 【用法2】记忆检索（RAI "回忆中" 阶段）
        relevant_memories = []
        if self._memory_service:
            try:
                relevant_memories = await self._memory_service.retrieve_relevant_memories(
                    user_id=conversation.user_id,
                    query=content,
                    limit=5
                )
                if relevant_memories:
                    logger.info(f"检索到 {len(relevant_memories)} 条相关记忆")
            except Exception as e:
                logger.warning(f"记忆检索失败: {e}")
        
        # 3. 构建Prompt并调用LLM（传入相关记忆）
        ai_response = await self._generate_ai_response(
            conversation=conversation,
            user_message=content,
            emotion_result=emotion_result,
            relevant_memories=relevant_memories
        )
        
        # 4. 保存AI回复
        ai_message = Message(
            id=f"msg_{uuid.uuid4().hex[:16]}",
            conversation_id=conversation_id,
            role=MessageRole.ASSISTANT,
            content=ai_response.content,
            tokens_used=ai_response.tokens_used,
            response_time_ms=int((datetime.utcnow() - start_time).total_seconds() * 1000),
            model=ai_response.model,
            created_at=datetime.utcnow()
        )
        await self._store.add_message(ai_message)
        
        # 4.5 【用法1】异步记忆提取（不阻塞回复）
        if self._memory_service:
            try:
                asyncio.create_task(
                    self._async_extract_memories(
                        user_id=conversation.user_id,
                        conversation_id=conversation_id,
                        user_message=content,
                        ai_response=ai_response.content
                    )
                )
            except Exception as e:
                logger.warning(f"启动记忆提取任务失败: {e}")
        
        # 5. 更新对话
        conversation.message_count = await self._store.get_message_count(conversation_id)
        conversation.updated_at = datetime.utcnow()
        conversation.last_message_at = datetime.utcnow()
        
        # 更新标题（如果是前几条消息）
        if conversation.message_count <= 2 and conversation.title == "新对话":
            conversation.title = self._generate_conversation_title(content)
        
        await self._store.update_conversation(conversation)
        
        logger.info(f"消息发送成功: 对话={conversation_id}, 用户消息={user_message.id}, AI消息={ai_message.id}")
        
        return ChatResponse(
            message_id=ai_message.id,
            conversation_id=conversation_id,
            user_message=user_message,
            ai_message=ai_message,
            emotion_analysis=emotion_result.to_dict() if emotion_result else None
        )
    
    async def _generate_ai_response(
        self,
        conversation: Conversation,
        user_message: str,
        emotion_result: Optional[Any] = None,
        relevant_memories: Optional[List[Dict]] = None
    ) -> Any:
        """生成AI回复
        
        Args:
            conversation: 对话对象
            user_message: 用户消息
            emotion_result: 情感分析结果
            relevant_memories: 相关记忆列表
            
        Returns:
            LLM响应
        """
        if not self._llm_service:
            raise ValueError("LLM服务未初始化")
        
        # 1. 构建系统提示词（传入相关记忆）
        system_prompt = await self._build_system_prompt(
            conversation=conversation,
            emotion_result=emotion_result,
            relevant_memories=relevant_memories
        )
        
        # 2. 获取对话历史
        history = await self._get_conversation_history(conversation.id, limit=10)
        
        # 3. 构建消息列表
        messages = []
        for msg in history:
            if msg.role == MessageRole.USER:
                messages.append({"role": "user", "content": msg.content})
            elif msg.role == MessageRole.ASSISTANT:
                messages.append({"role": "assistant", "content": msg.content})
        
        # 添加当前用户消息
        messages.append({"role": "user", "content": user_message})
        
        # 4. 调用LLM
        try:
            response = await self._llm_service.chat(
                messages=messages,
                system_prompt=system_prompt,
                temperature=0.7,
                max_tokens=2000
            )
            return response
        except Exception as e:
            logger.error(f"LLM调用失败: {e}")
            # 返回友好的错误消息
            raise
    
    async def _build_system_prompt(
        self,
        conversation: Conversation,
        emotion_result: Optional[Any] = None,
        relevant_memories: Optional[List[Dict]] = None
    ) -> str:
        """构建系统提示词
        
        Args:
            conversation: 对话对象
            emotion_result: 情感分析结果
            relevant_memories: 相关记忆列表
            
        Returns:
            系统提示词
        """
        try:
            from services.prompt_templates import get_system_prompt, get_emotion_response_prompt, EmotionType
            
            # 获取用户画像和优势档案
            user_profile = conversation.context.get("user_profile", {})
            strength_profile = conversation.context.get("strength_profile", {})
            
            # 构建基础系统提示词
            system_prompt = get_system_prompt(
                user_profile=user_profile,
                strength_profile=strength_profile,
                conversation_context=None
            )
            
            # 【用法2】添加相关记忆上下文
            if relevant_memories and len(relevant_memories) > 0:
                memory_context = "\n\n# 用户历史相关信息（从记忆中检索）\n"
                for i, mem in enumerate(relevant_memories, 1):
                    memory_context += f"{i}. {mem.get('memory', '')}\n"
                memory_context += "\n请基于以上历史背景，提供个性化、连贯的回复。如果用户表达了新的目标、偏好或重要信息，请在回复中自然确认。"
                system_prompt += memory_context
            
            # 如果有情感分析结果，添加情感回应指导
            if emotion_result:
                emotion_prompt = get_emotion_response_prompt(
                    emotion_type=EmotionType(emotion_result.emotion.value),
                    user_message="",  # 将在后续填充
                    emotion_description=emotion_result.emotion_label,
                    intensity=emotion_result.intensity
                )
                system_prompt += f"\n\n# 当前情感回应指导\n\n{emotion_prompt}"
            
            return system_prompt
        except Exception as e:
            logger.warning(f"构建系统提示词失败: {e}")
            # 返回默认提示词
            return "你是一位专业的优势教练，帮助用户发现和发挥个人优势。"
    
    async def _async_extract_memories(
        self,
        user_id: str,
        conversation_id: str,
        user_message: str,
        ai_response: str
    ):
        """
        【用法1】异步提取记忆（后台执行，不阻塞回复）
        
        从对话中提取关键信息并存储到 Mem0
        """
        try:
            messages = [
                {"role": "user", "content": user_message},
                {"role": "assistant", "content": ai_response}
            ]
            
            # 提取并存储记忆
            memories = await self._memory_service.extract_and_store_memories(
                user_id=user_id,
                conversation_id=conversation_id,
                messages=messages
            )
            
            if memories:
                logger.info(f"成功提取 {len(memories)} 条记忆")
                
                # 【用法3】同步到星图节点（L2 → L3）
                try:
                    await self._memory_service.sync_memories_to_star_nodes(
                        user_id=user_id,
                        memory_ids=[m["id"] for m in memories]
                    )
                    logger.info(f"成功同步 {len(memories)} 条记忆到星图")
                except Exception as e:
                    logger.warning(f"同步记忆到星图失败: {e}")
            
        except Exception as e:
            logger.warning(f"异步记忆提取失败: {e}")
    
    async def _get_conversation_history(
        self,
        conversation_id: str,
        limit: int = 10
    ) -> List[Message]:
        """获取对话历史
        
        Args:
            conversation_id: 对话ID
            limit: 消息数量限制
            
        Returns:
            消息列表
        """
        messages = await self._store.get_messages(conversation_id, limit=limit)
        return messages
    
    def _generate_conversation_title(self, first_message: str) -> str:
        """生成对话标题
        
        Args:
            first_message: 第一条消息
            
        Returns:
            对话标题
        """
        # 提取前20个字符作为标题
        title = first_message[:30] if len(first_message) <= 30 else first_message[:27] + "..."
        return title
    
    async def get_conversation(
        self,
        conversation_id: str,
        user_id: Optional[str] = None
    ) -> Optional[Conversation]:
        """获取对话详情
        
        Args:
            conversation_id: 对话ID
            user_id: 用户ID（用于验证）
            
        Returns:
            对话对象
        """
        conversation = await self._store.get_conversation(conversation_id)
        if not conversation:
            return None
        
        if user_id and conversation.user_id != user_id:
            raise PermissionError("无权访问此对话")
        
        return conversation
    
    async def get_conversation_history(
        self,
        conversation_id: str,
        user_id: Optional[str] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[Message]:
        """获取对话消息历史
        
        Args:
            conversation_id: 对话ID
            user_id: 用户ID（用于验证）
            limit: 消息数量限制
            offset: 偏移量
            
        Returns:
            消息列表
        """
        # 验证对话存在且用户有权限
        conversation = await self._store.get_conversation(conversation_id)
        if not conversation:
            raise ValueError(f"对话不存在: {conversation_id}")
        
        if user_id and conversation.user_id != user_id:
            raise PermissionError("无权访问此对话")
        
        return await self._store.get_messages(conversation_id, limit=limit, offset=offset)
    
    async def get_user_conversations(
        self,
        user_id: str,
        limit: int = 20,
        offset: int = 0
    ) -> List[Conversation]:
        """获取用户对话列表
        
        Args:
            user_id: 用户ID
            limit: 数量限制
            offset: 偏移量
            
        Returns:
            对话列表
        """
        return await self._store.list_user_conversations(user_id, limit=limit, offset=offset)
    
    async def delete_conversation(
        self,
        conversation_id: str,
        user_id: Optional[str] = None
    ) -> bool:
        """删除对话
        
        Args:
            conversation_id: 对话ID
            user_id: 用户ID（用于验证）
            
        Returns:
            是否删除成功
        """
        # 验证对话存在且用户有权限
        conversation = await self._store.get_conversation(conversation_id)
        if not conversation:
            return False
        
        if user_id and conversation.user_id != user_id:
            raise PermissionError("无权删除此对话")
        
        return await self._store.delete_conversation(conversation_id)
    
    async def update_conversation_title(
        self,
        conversation_id: str,
        title: str,
        user_id: Optional[str] = None
    ) -> Conversation:
        """更新对话标题
        
        Args:
            conversation_id: 对话ID
            title: 新标题
            user_id: 用户ID（用于验证）
            
        Returns:
            更新后的对话
        """
        conversation = await self._store.get_conversation(conversation_id)
        if not conversation:
            raise ValueError(f"对话不存在: {conversation_id}")
        
        if user_id and conversation.user_id != user_id:
            raise PermissionError("无权修改此对话")
        
        conversation.title = title
        conversation.updated_at = datetime.utcnow()
        
        return await self._store.update_conversation(conversation)
    
    async def generate_summary(
        self,
        conversation_id: str,
        user_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """生成对话摘要
        
        Args:
            conversation_id: 对话ID
            user_id: 用户ID（用于验证）
            
        Returns:
            摘要信息
        """
        # 获取对话和消息
        conversation = await self.get_conversation(conversation_id, user_id)
        if not conversation:
            raise ValueError(f"对话不存在: {conversation_id}")
        
        messages = await self.get_conversation_history(conversation_id, user_id, limit=100)
        
        # 统计信息
        user_message_count = sum(1 for m in messages if m.role == MessageRole.USER)
        ai_message_count = sum(1 for m in messages if m.role == MessageRole.ASSISTANT)
        
        # 提取关键主题（简单实现）
        all_content = " ".join([m.content for m in messages])
        
        # 使用LLM生成摘要
        summary_text = ""
        key_points = []
        action_items = []
        
        if self._llm_service and len(messages) > 2:
            try:
                summary_prompt = f"""请对以下对话进行摘要，提取关键要点和行动项：

对话内容：
{all_content[:2000]}

请以JSON格式返回：
{{
    "summary": "对话摘要（100字以内）",
    "key_points": ["要点1", "要点2", ...],
    "action_items": ["行动项1", "行动项2", ...]
}}"""
                
                response = await self._llm_service.chat(
                    messages=[{"role": "user", "content": summary_prompt}],
                    temperature=0.3,
                    max_tokens=500
                )
                
                # 解析JSON响应
                import json
                try:
                    result = json.loads(response.content)
                    summary_text = result.get("summary", "")
                    key_points = result.get("key_points", [])
                    action_items = result.get("action_items", [])
                except json.JSONDecodeError:
                    summary_text = response.content[:200]
            except Exception as e:
                logger.warning(f"生成摘要失败: {e}")
        
        return {
            "conversation_id": conversation_id,
            "title": conversation.title,
            "message_count": len(messages),
            "user_message_count": user_message_count,
            "ai_message_count": ai_message_count,
            "summary": summary_text or f"本对话共{len(messages)}条消息",
            "key_points": key_points,
            "action_items": action_items,
            "created_at": conversation.created_at.isoformat(),
            "last_message_at": conversation.last_message_at.isoformat() if conversation.last_message_at else None
        }
    
    async def check_quota(self, user_id: str) -> Dict[str, Any]:
        """检查用户对话配额
        
        Args:
            user_id: 用户ID
            
        Returns:
            配额信息
        """
        # 获取用户今天的对话数
        today = datetime.utcnow().date()
        
        # 获取用户对话列表
        conversations = await self.get_user_conversations(user_id, limit=1000)
        
        # 统计今日消息数
        today_message_count = 0
        for conv in conversations:
            if conv.last_message_at and conv.last_message_at.date() == today:
                messages = await self._store.get_messages(conv.id)
                today_message_count += len([m for m in messages if m.created_at.date() == today])
        
        # 默认配额：免费用户每日100条消息
        daily_limit = 100
        remaining = max(0, daily_limit - today_message_count)
        
        return {
            "daily_limit": daily_limit,
            "used_today": today_message_count,
            "remaining": remaining,
            "has_quota": remaining > 0
        }


# =============================================================================
# 便捷函数和全局实例
# =============================================================================

_chat_service: Optional[ChatService] = None


def get_chat_service() -> ChatService:
    """获取全局对话服务实例
    
    Returns:
        ChatService实例
    """
    global _chat_service
    if _chat_service is None:
        _chat_service = ChatService()
    return _chat_service


def init_chat_service(
    llm_service=None,
    emotion_analyzer=None,
    conversation_store=None
) -> ChatService:
    """初始化对话服务
    
    Args:
        llm_service: LLM服务实例
        emotion_analyzer: 情感分析器实例
        conversation_store: 对话存储实例
        
    Returns:
        ChatService实例
    """
    global _chat_service
    _chat_service = ChatService(
        llm_service=llm_service,
        emotion_analyzer=emotion_analyzer,
        conversation_store=conversation_store
    )
    return _chat_service
