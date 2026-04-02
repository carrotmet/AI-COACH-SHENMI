# -*- coding: utf-8 -*-
"""
深觅 AI Coach - 统一响应格式模块

该模块提供：
- 统一响应格式：{code, message, data}
- 错误响应格式
- 业务错误码定义
"""

from enum import IntEnum
from typing import Any, Optional, Dict, TypeVar, Generic
from datetime import datetime

from pydantic import BaseModel, Field


# =====================================================
# 业务错误码定义
# =====================================================
class ResponseCode(IntEnum):
    """
    API响应状态码
    
    格式: XXYY
    - XX: 模块编号 (00通用, 01用户, 02认证, 03测评, 04对话, 05订阅)
    - YY: 具体错误码
    """
    # 成功 (0)
    SUCCESS = 200
    CREATED = 201
    ACCEPTED = 202
    
    # 通用错误 (1000-1099)
    BAD_REQUEST = 1000
    UNAUTHORIZED = 1001
    FORBIDDEN = 1002
    NOT_FOUND = 1003
    METHOD_NOT_ALLOWED = 1004
    CONFLICT = 1005
    UNPROCESSABLE_ENTITY = 1006
    TOO_MANY_REQUESTS = 1007
    INTERNAL_ERROR = 1008
    SERVICE_UNAVAILABLE = 1009
    
    # 用户相关错误 (1100-1199)
    USER_NOT_FOUND = 1100
    USER_ALREADY_EXISTS = 1101
    USER_INACTIVE = 1102
    USER_SUSPENDED = 1103
    USER_DELETED = 1104
    
    # 认证相关错误 (1200-1299)
    INVALID_CREDENTIALS = 1200
    INVALID_TOKEN = 1201
    TOKEN_EXPIRED = 1202
    INVALID_REFRESH_TOKEN = 1203
    REFRESH_TOKEN_EXPIRED = 1204
    PASSWORD_TOO_WEAK = 1205
    PASSWORD_INCORRECT = 1206
    
    # 测评相关错误 (1300-1399)
    ASSESSMENT_NOT_FOUND = 1300
    ASSESSMENT_ALREADY_COMPLETED = 1301
    ASSESSMENT_INVALID_ANSWER = 1302
    ASSESSMENT_QUOTA_EXCEEDED = 1303
    
    # 对话相关错误 (1400-1499)
    CONVERSATION_NOT_FOUND = 1400
    MESSAGE_SEND_FAILED = 1401
    CONVERSATION_LIMIT_REACHED = 1402
    MESSAGE_LIMIT_REACHED = 1403
    AI_SERVICE_ERROR = 1404
    
    # 订阅相关错误 (1500-1599)
    SUBSCRIPTION_EXPIRED = 1500
    SUBSCRIPTION_QUOTA_EXCEEDED = 1501
    PAYMENT_FAILED = 1502
    PLAN_NOT_FOUND = 1503


# =====================================================
# 错误码消息映射
# =====================================================
RESPONSE_MESSAGES: Dict[ResponseCode, str] = {
    # 成功
    ResponseCode.SUCCESS: "请求成功",
    ResponseCode.CREATED: "创建成功",
    ResponseCode.ACCEPTED: "请求已接受",
    
    # 通用错误
    ResponseCode.BAD_REQUEST: "请求参数错误",
    ResponseCode.UNAUTHORIZED: "未授权，请先登录",
    ResponseCode.FORBIDDEN: "无权限访问",
    ResponseCode.NOT_FOUND: "资源不存在",
    ResponseCode.METHOD_NOT_ALLOWED: "请求方法不允许",
    ResponseCode.CONFLICT: "资源冲突",
    ResponseCode.UNPROCESSABLE_ENTITY: "请求数据验证失败",
    ResponseCode.TOO_MANY_REQUESTS: "请求过于频繁，请稍后重试",
    ResponseCode.INTERNAL_ERROR: "服务器内部错误",
    ResponseCode.SERVICE_UNAVAILABLE: "服务暂不可用",
    
    # 用户相关
    ResponseCode.USER_NOT_FOUND: "用户不存在",
    ResponseCode.USER_ALREADY_EXISTS: "用户已存在",
    ResponseCode.USER_INACTIVE: "用户未激活",
    ResponseCode.USER_SUSPENDED: "用户已被暂停",
    ResponseCode.USER_DELETED: "用户已删除",
    
    # 认证相关
    ResponseCode.INVALID_CREDENTIALS: "用户名或密码错误",
    ResponseCode.INVALID_TOKEN: "Token无效",
    ResponseCode.TOKEN_EXPIRED: "Token已过期",
    ResponseCode.INVALID_REFRESH_TOKEN: "刷新Token无效",
    ResponseCode.REFRESH_TOKEN_EXPIRED: "刷新Token已过期",
    ResponseCode.PASSWORD_TOO_WEAK: "密码强度不足",
    ResponseCode.PASSWORD_INCORRECT: "密码不正确",
    
    # 测评相关
    ResponseCode.ASSESSMENT_NOT_FOUND: "测评不存在",
    ResponseCode.ASSESSMENT_ALREADY_COMPLETED: "测评已完成",
    ResponseCode.ASSESSMENT_INVALID_ANSWER: "答案格式无效",
    ResponseCode.ASSESSMENT_QUOTA_EXCEEDED: "测评次数已用完",
    
    # 对话相关
    ResponseCode.CONVERSATION_NOT_FOUND: "对话不存在",
    ResponseCode.MESSAGE_SEND_FAILED: "消息发送失败",
    ResponseCode.CONVERSATION_LIMIT_REACHED: "对话数量已达上限",
    ResponseCode.MESSAGE_LIMIT_REACHED: "消息数量已达上限",
    ResponseCode.AI_SERVICE_ERROR: "AI服务调用失败",
    
    # 订阅相关
    ResponseCode.SUBSCRIPTION_EXPIRED: "订阅已过期",
    ResponseCode.SUBSCRIPTION_QUOTA_EXCEEDED: "订阅配额已用完",
    ResponseCode.PAYMENT_FAILED: "支付失败",
    ResponseCode.PLAN_NOT_FOUND: "套餐不存在",
}


def get_message_by_code(code: ResponseCode) -> str:
    """
    根据错误码获取默认消息
    
    Args:
        code: 响应状态码
        
    Returns:
        str: 对应的默认消息
    """
    return RESPONSE_MESSAGES.get(code, "未知错误")


# =====================================================
# Pydantic响应模型
# =====================================================
T = TypeVar('T')


class ApiResponse(BaseModel, Generic[T]):
    """
    统一API响应模型
    
    Attributes:
        code: 业务状态码
        message: 响应消息
        data: 响应数据
        timestamp: 响应时间戳
    """
    code: int = Field(default=ResponseCode.SUCCESS, description="业务状态码")
    message: str = Field(default="请求成功", description="响应消息")
    data: Optional[T] = Field(default=None, description="响应数据")
    timestamp: str = Field(default_factory=lambda: datetime.utcnow().isoformat(), description="响应时间戳")
    
    class Config:
        json_schema_extra = {
            "example": {
                "code": 200,
                "message": "请求成功",
                "data": {},
                "timestamp": "2024-01-15T10:30:00.000000"
            }
        }


class ErrorDetail(BaseModel):
    """错误详情模型"""
    field: Optional[str] = Field(default=None, description="错误字段")
    message: str = Field(description="错误描述")
    
    class Config:
        json_schema_extra = {
            "example": {
                "field": "email",
                "message": "邮箱格式不正确"
            }
        }


class ErrorResponse(BaseModel):
    """
    错误响应模型
    
    Attributes:
        code: 错误码
        message: 错误消息
        detail: 详细错误信息
        timestamp: 响应时间戳
    """
    code: int = Field(description="错误码")
    message: str = Field(description="错误消息")
    detail: Optional[str] = Field(default=None, description="详细错误信息")
    errors: Optional[list] = Field(default=None, description="字段错误列表")
    timestamp: str = Field(default_factory=lambda: datetime.utcnow().isoformat(), description="响应时间戳")
    
    class Config:
        json_schema_extra = {
            "example": {
                "code": 1101,
                "message": "用户已存在",
                "detail": "该邮箱已被注册",
                "timestamp": "2024-01-15T10:30:00.000000"
            }
        }


# =====================================================
# 响应构建函数
# =====================================================

def success_response(
    data: Any = None,
    message: str = "请求成功",
    code: ResponseCode = ResponseCode.SUCCESS
) -> Dict[str, Any]:
    """
    构建成功响应
    
    Args:
        data: 响应数据
        message: 响应消息
        code: 状态码
        
    Returns:
        Dict: 统一格式的成功响应
    """
    return {
        "code": code,
        "message": message,
        "data": data,
        "timestamp": datetime.utcnow().isoformat()
    }


def error_response(
    code: ResponseCode,
    message: Optional[str] = None,
    detail: Optional[str] = None,
    errors: Optional[list] = None
) -> Dict[str, Any]:
    """
    构建错误响应
    
    Args:
        code: 错误码
        message: 错误消息，默认使用错误码对应的消息
        detail: 详细错误信息
        errors: 字段错误列表
        
    Returns:
        Dict: 统一格式的错误响应
    """
    return {
        "code": code,
        "message": message or get_message_by_code(code),
        "detail": detail,
        "errors": errors,
        "timestamp": datetime.utcnow().isoformat()
    }


def created_response(
    data: Any = None,
    message: str = "创建成功"
) -> Dict[str, Any]:
    """
    构建创建成功响应
    
    Args:
        data: 响应数据
        message: 响应消息
        
    Returns:
        Dict: 统一格式的创建成功响应
    """
    return success_response(data=data, message=message, code=ResponseCode.CREATED)


def paginated_response(
    items: list,
    total: int,
    page: int,
    limit: int,
    message: str = "请求成功"
) -> Dict[str, Any]:
    """
    构建分页响应
    
    Args:
        items: 数据列表
        total: 总记录数
        page: 当前页码
        limit: 每页数量
        message: 响应消息
        
    Returns:
        Dict: 统一格式的分页响应
    """
    return success_response(
        data={
            "items": items,
            "total": total,
            "page": page,
            "limit": limit,
            "total_pages": (total + limit - 1) // limit if limit > 0 else 0
        },
        message=message
    )
