# -*- coding: utf-8 -*-
"""
深觅 AI Coach - 对话路由

本模块提供对话系统的API路由：
- POST /conversations - 创建对话
- GET /conversations - 获取用户对话列表
- GET /conversations/{id} - 获取对话详情
- POST /conversations/{id}/messages - 发送消息
- GET /conversations/{id}/messages - 获取消息历史
- DELETE /conversations/{id} - 删除对话
- GET /conversations/{id}/summary - 获取对话摘要
- GET /conversations/limits - 获取对话限制
"""

from typing import List, Optional, Any
from datetime import datetime
from pydantic import BaseModel, Field
from fastapi import APIRouter, Depends, HTTPException, status, Query
from fastapi.responses import JSONResponse
import logging

# 配置日志
logger = logging.getLogger(__name__)

# 导入统一响应工具
from utils.response import success_response, created_response, error_response

# 创建路由
router = APIRouter(tags=["对话系统"])


# =============================================================================
# Pydantic模型定义
# =============================================================================

class CreateConversationRequest(BaseModel):
    """创建对话请求"""
    title: Optional[str] = Field(None, description="对话标题")
    context: Optional[dict] = Field(None, description="对话上下文")
    coach_type: str = Field(default="strength", description="教练类型")
    
    class Config:
        json_schema_extra = {
            "example": {
                "title": "优势探索对话",
                "context": {
                    "assessment_id": "asm_123456",
                    "top_strengths": ["战略思维", "学习力"]
                },
                "coach_type": "strength"
            }
        }


class CreateConversationResponse(BaseModel):
    """创建对话响应"""
    conversation_id: str = Field(..., description="对话ID")
    title: str = Field(..., description="对话标题")
    created_at: str = Field(..., description="创建时间")
    
    class Config:
        json_schema_extra = {
            "example": {
                "conversation_id": "conv_123456789",
                "title": "优势探索对话",
                "created_at": "2024-01-20T11:00:00Z"
            }
        }


class ConversationListItem(BaseModel):
    """对话列表项"""
    conversation_id: str = Field(..., description="对话ID")
    title: str = Field(..., description="对话标题")
    message_count: int = Field(..., description="消息数量")
    created_at: str = Field(..., description="创建时间")
    updated_at: str = Field(..., description="更新时间")
    last_message_at: Optional[str] = Field(None, description="最后消息时间")


class ConversationListResponse(BaseModel):
    """对话列表响应"""
    items: List[ConversationListItem] = Field(..., description="对话列表")
    total: int = Field(..., description="总数")
    page: int = Field(..., description="当前页码")
    limit: int = Field(..., description="每页数量")


class ConversationDetailResponse(BaseModel):
    """对话详情响应"""
    conversation_id: str = Field(..., description="对话ID")
    user_id: str = Field(..., description="用户ID")
    title: str = Field(..., description="对话标题")
    status: str = Field(..., description="状态")
    coach_type: str = Field(..., description="教练类型")
    context: dict = Field(..., description="对话上下文")
    message_count: int = Field(..., description="消息数量")
    created_at: str = Field(..., description="创建时间")
    updated_at: str = Field(..., description="更新时间")
    last_message_at: Optional[str] = Field(None, description="最后消息时间")


class SendMessageRequest(BaseModel):
    """发送消息请求"""
    content: str = Field(..., min_length=1, max_length=5000, description="消息内容")
    type: str = Field(default="text", description="消息类型")
    
    class Config:
        json_schema_extra = {
            "example": {
                "content": "我想了解更多关于战略思维的优势如何应用",
                "type": "text"
            }
        }


class MessageResponse(BaseModel):
    """消息响应"""
    id: str = Field(..., description="消息ID")
    role: str = Field(..., description="角色")
    content: str = Field(..., description="内容")
    emotion_tag: Optional[str] = Field(None, description="情感标签")
    sentiment_score: Optional[float] = Field(None, description="情感分数")
    tokens_used: int = Field(0, description="Token使用量")
    response_time_ms: int = Field(0, description="响应时间")
    model: Optional[str] = Field(None, description="模型")
    created_at: str = Field(..., description="创建时间")


class SendMessageResponse(BaseModel):
    """发送消息响应"""
    message_id: str = Field(..., description="消息ID")
    conversation_id: str = Field(..., description="对话ID")
    user_message: MessageResponse = Field(..., description="用户消息")
    ai_message: MessageResponse = Field(..., description="AI消息")
    emotion_analysis: Optional[dict] = Field(None, description="情感分析")
    timestamp: str = Field(..., description="时间戳")


class MessageListResponse(BaseModel):
    """消息列表响应"""
    conversation_id: str = Field(..., description="对话ID")
    messages: List[MessageResponse] = Field(..., description="消息列表")
    total: int = Field(..., description="总数")
    page: int = Field(..., description="当前页码")
    limit: int = Field(..., description="每页数量")


class ConversationSummaryResponse(BaseModel):
    """对话摘要响应"""
    conversation_id: str = Field(..., description="对话ID")
    title: str = Field(..., description="对话标题")
    message_count: int = Field(..., description="消息数量")
    user_message_count: int = Field(..., description="用户消息数")
    ai_message_count: int = Field(..., description="AI消息数")
    summary: str = Field(..., description="摘要")
    key_points: List[str] = Field(default_factory=list, description="关键要点")
    action_items: List[str] = Field(default_factory=list, description="行动项")
    created_at: str = Field(..., description="创建时间")
    last_message_at: Optional[str] = Field(None, description="最后消息时间")


class ConversationLimitsResponse(BaseModel):
    """对话限制响应"""
    daily_limit: int = Field(..., description="每日限制")
    used_today: int = Field(..., description="今日已用")
    remaining: int = Field(..., description="剩余次数")
    has_quota: bool = Field(..., description="是否有配额")


class ErrorResponse(BaseModel):
    """错误响应"""
    code: int = Field(..., description="错误码")
    message: str = Field(..., description="错误信息")
    detail: Optional[str] = Field(None, description="详细说明")


# =============================================================================
# 依赖注入函数（模拟，实际项目中应从认证系统获取）
# =============================================================================

async def get_current_user_id() -> str:
    """获取当前用户ID
    
    实际项目中应从JWT Token或Session中获取
    
    Returns:
        用户ID
    """
    # 模拟用户ID，实际应从认证系统获取
    return "user_123456"


async def get_chat_service() -> Any:
    """获取对话服务实例
    
    Returns:
        ChatService实例
    """
    from services.chat_service import get_chat_service
    return get_chat_service()


# =============================================================================
# API路由
# =============================================================================

@router.post(
    "",
    status_code=status.HTTP_201_CREATED,
    summary="创建对话",
    description="创建新的对话会话",
    responses={
        201: {"description": "创建成功"},
        401: {"description": "未认证", "model": ErrorResponse}
    }
)
async def create_conversation(
    request: CreateConversationRequest,
    user_id: str = Depends(get_current_user_id),
    chat_service = Depends(get_chat_service)
):
    """创建新对话
    
    创建一个新的AI教练对话会话
    """
    try:
        # 创建对话（不检查配额，空对话不消耗AI调用）
        conversation = await chat_service.create_conversation(
            user_id=user_id,
            title=request.title,
            context=request.context,
            coach_type=request.coach_type
        )
        
        return created_response(data={
            "conversation_id": conversation.id,
            "title": conversation.title,
            "created_at": conversation.created_at.isoformat()
        })
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"创建对话失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "code": 3001,
                "message": "创建对话失败",
                "detail": str(e)
            }
        )


@router.get(
    "",
    response_model=ConversationListResponse,
    summary="获取对话列表",
    description="获取当前用户的对话列表",
    responses={
        200: {"description": "获取成功"},
        401: {"description": "未认证", "model": ErrorResponse}
    }
)
async def get_conversations(
    page: int = Query(default=1, ge=1, description="页码"),
    limit: int = Query(default=20, ge=1, le=100, description="每页数量"),
    user_id: str = Depends(get_current_user_id),
    chat_service = Depends(get_chat_service)
):
    """获取用户对话列表
    
    获取当前用户的所有对话会话列表
    """
    try:
        offset = (page - 1) * limit
        conversations = await chat_service.get_user_conversations(
            user_id=user_id,
            limit=limit,
            offset=offset
        )
        
        # 获取总数（简化实现）
        all_conversations = await chat_service.get_user_conversations(
            user_id=user_id,
            limit=1000
        )
        total = len(all_conversations)
        
        items = [
            ConversationListItem(
                conversation_id=conv.id,
                title=conv.title,
                message_count=conv.message_count,
                created_at=conv.created_at.isoformat(),
                updated_at=conv.updated_at.isoformat(),
                last_message_at=conv.last_message_at.isoformat() if conv.last_message_at else None
            )
            for conv in conversations
        ]
        
        return ConversationListResponse(
            items=items,
            total=total,
            page=page,
            limit=limit
        )
    
    except Exception as e:
        logger.error(f"获取对话列表失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "code": 3001,
                "message": "获取对话列表失败",
                "detail": str(e)
            }
        )


@router.get(
    "/{conversation_id}",
    response_model=ConversationDetailResponse,
    summary="获取对话详情",
    description="获取指定对话的详细信息",
    responses={
        200: {"description": "获取成功"},
        401: {"description": "未认证", "model": ErrorResponse},
        404: {"description": "对话不存在", "model": ErrorResponse}
    }
)
async def get_conversation(
    conversation_id: str,
    user_id: str = Depends(get_current_user_id),
    chat_service = Depends(get_chat_service)
):
    """获取对话详情
    
    获取指定对话的详细信息和元数据
    """
    try:
        conversation = await chat_service.get_conversation(
            conversation_id=conversation_id,
            user_id=user_id
        )
        
        if not conversation:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={
                    "code": 3001,
                    "message": "对话不存在",
                    "detail": f"对话ID {conversation_id} 不存在或已删除"
                }
            )
        
        return ConversationDetailResponse(
            conversation_id=conversation.id,
            user_id=conversation.user_id,
            title=conversation.title,
            status=conversation.status.value,
            coach_type=conversation.coach_type,
            context=conversation.context,
            message_count=conversation.message_count,
            created_at=conversation.created_at.isoformat(),
            updated_at=conversation.updated_at.isoformat(),
            last_message_at=conversation.last_message_at.isoformat() if conversation.last_message_at else None
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取对话详情失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "code": 3001,
                "message": "获取对话详情失败",
                "detail": str(e)
            }
        )


@router.post(
    "/{conversation_id}/messages",
    summary="发送消息",
    description="向指定对话发送消息并获取AI回复",
    responses={
        200: {"description": "发送成功"},
        401: {"description": "未认证", "model": ErrorResponse},
        404: {"description": "对话不存在", "model": ErrorResponse},
        429: {"description": "超出配额限制", "model": ErrorResponse},
        500: {"description": "AI服务错误", "model": ErrorResponse}
    }
)
async def send_message(
    conversation_id: str,
    request: SendMessageRequest,
    user_id: str = Depends(get_current_user_id),
    chat_service = Depends(get_chat_service)
):
    """发送消息
    
    向指定对话发送消息，AI教练会生成回复
    """
    try:
        # 检查配额
        quota = await chat_service.check_quota(user_id)
        if not quota["has_quota"]:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail={
                    "code": 4002,
                    "message": "对话次数不足",
                    "detail": "今日对话次数已用完，请明天再来或升级订阅"
                }
            )
        
        # 发送消息
        response = await chat_service.send_message(
            conversation_id=conversation_id,
            content=request.content,
            user_id=user_id
        )
        
        return success_response(data={
            "message_id": response.message_id,
            "conversation_id": response.conversation_id,
            "user_message": {
                "id": response.user_message.id,
                "role": response.user_message.role.value,
                "content": response.user_message.content,
                "emotion_tag": response.user_message.emotion_tag,
                "sentiment_score": response.user_message.sentiment_score,
                "tokens_used": response.user_message.tokens_used,
                "response_time_ms": response.user_message.response_time_ms,
                "model": response.user_message.model,
                "created_at": response.user_message.created_at.isoformat()
            },
            "ai_message": {
                "id": response.ai_message.id,
                "role": response.ai_message.role.value,
                "content": response.ai_message.content,
                "emotion_tag": response.ai_message.emotion_tag,
                "sentiment_score": response.ai_message.sentiment_score,
                "tokens_used": response.ai_message.tokens_used,
                "response_time_ms": response.ai_message.response_time_ms,
                "model": response.ai_message.model,
                "created_at": response.ai_message.created_at.isoformat()
            },
            "emotion_analysis": response.emotion_analysis,
            "timestamp": datetime.utcnow().isoformat()
        })
    
    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "code": 3001,
                "message": "对话不存在",
                "detail": str(e)
            }
        )
    except PermissionError as e:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "code": 1004,
                "message": "无权访问",
                "detail": str(e)
            }
        )
    except Exception as e:
        logger.error(f"发送消息失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "code": 3002,
                "message": "消息发送失败",
                "detail": f"AI服务暂时不可用: {str(e)}"
            }
        )


@router.get(
    "/{conversation_id}/messages",
    response_model=MessageListResponse,
    summary="获取消息历史",
    description="获取指定对话的消息历史",
    responses={
        200: {"description": "获取成功"},
        401: {"description": "未认证", "model": ErrorResponse},
        404: {"description": "对话不存在", "model": ErrorResponse}
    }
)
async def get_messages(
    conversation_id: str,
    page: int = Query(default=1, ge=1, description="页码"),
    limit: int = Query(default=20, ge=1, le=100, description="每页数量"),
    user_id: str = Depends(get_current_user_id),
    chat_service = Depends(get_chat_service)
):
    """获取消息历史
    
    获取指定对话的所有消息记录
    """
    try:
        offset = (page - 1) * limit
        messages = await chat_service.get_conversation_history(
            conversation_id=conversation_id,
            user_id=user_id,
            limit=limit,
            offset=offset
        )
        
        # 获取总数
        all_messages = await chat_service.get_conversation_history(
            conversation_id=conversation_id,
            user_id=user_id,
            limit=1000
        )
        total = len(all_messages)
        
        message_responses = [
            MessageResponse(
                id=msg.id,
                role=msg.role.value,
                content=msg.content,
                emotion_tag=msg.emotion_tag,
                sentiment_score=msg.sentiment_score,
                tokens_used=msg.tokens_used,
                response_time_ms=msg.response_time_ms,
                model=msg.model,
                created_at=msg.created_at.isoformat()
            )
            for msg in messages
        ]
        
        return MessageListResponse(
            conversation_id=conversation_id,
            messages=message_responses,
            total=total,
            page=page,
            limit=limit
        )
    
    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "code": 3001,
                "message": "对话不存在",
                "detail": str(e)
            }
        )
    except PermissionError as e:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "code": 1004,
                "message": "无权访问",
                "detail": str(e)
            }
        )
    except Exception as e:
        logger.error(f"获取消息历史失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "code": 3001,
                "message": "获取消息历史失败",
                "detail": str(e)
            }
        )


@router.delete(
    "/{conversation_id}",
    summary="删除对话",
    description="删除指定的对话会话",
    responses={
        200: {"description": "删除成功"},
        401: {"description": "未认证", "model": ErrorResponse},
        404: {"description": "对话不存在", "model": ErrorResponse}
    }
)
async def delete_conversation(
    conversation_id: str,
    user_id: str = Depends(get_current_user_id),
    chat_service = Depends(get_chat_service)
):
    """删除对话
    
    删除指定的对话会话及其所有消息
    """
    try:
        success = await chat_service.delete_conversation(
            conversation_id=conversation_id,
            user_id=user_id
        )
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={
                    "code": 3001,
                    "message": "对话不存在",
                    "detail": f"对话ID {conversation_id} 不存在或已删除"
                }
            )
        
        return {
            "code": 200,
            "data": {
                "message": "对话已删除"
            }
        }
    
    except HTTPException:
        raise
    except PermissionError as e:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "code": 1004,
                "message": "无权删除",
                "detail": str(e)
            }
        )
    except Exception as e:
        logger.error(f"删除对话失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "code": 3001,
                "message": "删除对话失败",
                "detail": str(e)
            }
        )


@router.get(
    "/{conversation_id}/summary",
    response_model=ConversationSummaryResponse,
    summary="获取对话摘要",
    description="获取指定对话的AI生成摘要",
    responses={
        200: {"description": "获取成功"},
        401: {"description": "未认证", "model": ErrorResponse},
        404: {"description": "对话不存在", "model": ErrorResponse}
    }
)
async def get_conversation_summary(
    conversation_id: str,
    user_id: str = Depends(get_current_user_id),
    chat_service = Depends(get_chat_service)
):
    """获取对话摘要
    
    获取指定对话的AI生成摘要，包括关键要点和行动项
    """
    try:
        summary = await chat_service.generate_summary(
            conversation_id=conversation_id,
            user_id=user_id
        )
        
        return ConversationSummaryResponse(
            conversation_id=summary["conversation_id"],
            title=summary["title"],
            message_count=summary["message_count"],
            user_message_count=summary["user_message_count"],
            ai_message_count=summary["ai_message_count"],
            summary=summary["summary"],
            key_points=summary.get("key_points", []),
            action_items=summary.get("action_items", []),
            created_at=summary["created_at"],
            last_message_at=summary.get("last_message_at")
        )
    
    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "code": 3001,
                "message": "对话不存在",
                "detail": str(e)
            }
        )
    except PermissionError as e:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "code": 1004,
                "message": "无权访问",
                "detail": str(e)
            }
        )
    except Exception as e:
        logger.error(f"获取对话摘要失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "code": 3001,
                "message": "获取对话摘要失败",
                "detail": str(e)
            }
        )


@router.get(
    "/limits",
    response_model=ConversationLimitsResponse,
    summary="获取对话限制",
    description="获取当前用户的对话配额信息",
    responses={
        200: {"description": "获取成功"},
        401: {"description": "未认证", "model": ErrorResponse}
    }
)
async def get_conversation_limits(
    user_id: str = Depends(get_current_user_id),
    chat_service = Depends(get_chat_service)
):
    """获取对话限制
    
    获取当前用户的对话配额使用情况
    """
    try:
        quota = await chat_service.check_quota(user_id)
        
        return ConversationLimitsResponse(
            daily_limit=quota["daily_limit"],
            used_today=quota["used_today"],
            remaining=quota["remaining"],
            has_quota=quota["has_quota"]
        )
    
    except Exception as e:
        logger.error(f"获取对话限制失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "code": 3001,
                "message": "获取对话限制失败",
                "detail": str(e)
            }
        )
