# -*- coding: utf-8 -*-
"""
深觅 AI Coach - 认证中间件

该模块提供：
- JWT Token验证中间件
- 当前用户获取依赖
"""

from typing import Optional
from fastapi import Request, HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession

from database.connection import get_db_session
from database.models import User, UserProfile
from utils.security import decode_token
from utils.response import ResponseCode, error_response


# =====================================================
# 安全方案
# =====================================================
security = HTTPBearer(auto_error=False)


class AuthMiddleware:
    """
    认证中间件
    
    验证请求中的JWT Token
    """
    
    def __init__(self, app):
        self.app = app
    
    async def __call__(self, scope, receive, send):
        """中间件调用"""
        await self.app(scope, receive, send)


# =====================================================
# 依赖函数
# =====================================================

async def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    db: AsyncSession = Depends(get_db_session)
) -> dict:
    """
    获取当前登录用户
    
    FastAPI依赖函数，用于验证Token并获取当前用户
    
    Args:
        credentials: HTTP认证凭证
        db: 数据库会话
        
    Returns:
        dict: 用户信息字典
        
    Raises:
        HTTPException: 认证失败时抛出401错误
    """
    # 检查凭证是否存在
    if credentials is None:
        raise HTTPException(
            status_code=401,
            detail=error_response(
                code=ResponseCode.UNAUTHORIZED,
                message="未提供认证凭证"
            )
        )
    
    # 获取Token
    token = credentials.credentials
    
    # 解码Token
    payload = decode_token(token)
    
    if payload is None:
        raise HTTPException(
            status_code=401,
            detail=error_response(
                code=ResponseCode.INVALID_TOKEN,
                message="Token无效或已过期"
            )
        )
    
    # 检查Token类型
    token_type = payload.get("type")
    if token_type != "access":
        raise HTTPException(
            status_code=401,
            detail=error_response(
                code=ResponseCode.INVALID_TOKEN,
                message="无效的Token类型"
            )
        )
    
    # 获取用户ID
    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(
            status_code=401,
            detail=error_response(
                code=ResponseCode.INVALID_TOKEN,
                message="Token数据无效"
            )
        )
    
    # 查询用户
    from sqlalchemy import select
    result = await db.execute(
        select(User).where(User.id == int(user_id))
    )
    user = result.scalar_one_or_none()
    
    if user is None:
        raise HTTPException(
            status_code=401,
            detail=error_response(
                code=ResponseCode.USER_NOT_FOUND,
                message="用户不存在"
            )
        )
    
    # 检查用户状态
    if user.status != "active":
        raise HTTPException(
            status_code=401,
            detail=error_response(
                code=ResponseCode.USER_INACTIVE,
                message="用户状态异常"
            )
        )
    
    # 获取用户画像
    profile_result = await db.execute(
        select(UserProfile).where(UserProfile.user_id == user.id)
    )
    profile = profile_result.scalar_one_or_none()
    
    # 返回用户信息
    return {
        "id": user.id,
        "username": user.username,
        "email": user.email,
        "nickname": profile.nickname if profile else user.username,
        "avatar_url": user.avatar_url,
        "subscription_type": user.subscription_type,
        "status": user.status,
    }


async def get_optional_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    db: AsyncSession = Depends(get_db_session)
) -> Optional[dict]:
    """
    可选的用户认证
    
    验证Token但不强制要求，用于可选登录的接口
    
    Args:
        credentials: HTTP认证凭证
        db: 数据库会话
        
    Returns:
        Optional[dict]: 用户信息，未认证返回None
    """
    if credentials is None:
        return None
    
    try:
        return await get_current_user(credentials, db)
    except HTTPException:
        return None


async def require_active_user(
    current_user: dict = Depends(get_current_user)
) -> dict:
    """
    要求活跃用户
    
    确保用户处于活跃状态
    
    Args:
        current_user: 当前用户信息
        
    Returns:
        dict: 用户信息
        
    Raises:
        HTTPException: 用户不活跃时抛出
    """
    if current_user.get("status") != "active":
        raise HTTPException(
            status_code=403,
            detail=error_response(
                code=ResponseCode.FORBIDDEN,
                message="用户账户未激活"
            )
        )
    return current_user
