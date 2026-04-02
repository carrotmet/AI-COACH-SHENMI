# -*- coding: utf-8 -*-
"""
深觅 AI Coach - 认证路由模块

该模块提供用户认证相关的API接口：
- POST /auth/register - 用户注册
- POST /auth/login - 用户登录
- POST /auth/logout - 用户登出
- POST /auth/refresh - 刷新Token
"""

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field, EmailStr
from sqlalchemy.ext.asyncio import AsyncSession

from database.connection import get_db_session
from services.auth_service import AuthService
from middleware.auth_middleware import get_current_user
from utils.response import (
    success_response,
    error_response,
    created_response,
    ResponseCode,
    ApiResponse,
)


# =====================================================
# 路由定义
# =====================================================
router = APIRouter(
    tags=["认证"],
    responses={
        401: {"description": "未授权"},
        403: {"description": "无权限"},
    }
)


# =====================================================
# 请求模型
# =====================================================

class RegisterRequest(BaseModel):
    """用户注册请求"""
    email: EmailStr = Field(..., description="用户邮箱")
    password: str = Field(
        ...,
        min_length=6,
        max_length=20,
        description="密码(6-20位)"
    )
    username: Optional[str] = Field(None, description="用户名")
    nickname: Optional[str] = Field(None, description="用户昵称")
    
    class Config:
        json_schema_extra = {
            "example": {
                "email": "user@example.com",
                "password": "password123",
                "nickname": "小明"
            }
        }


class LoginRequest(BaseModel):
    """用户登录请求"""
    email: EmailStr = Field(..., description="用户邮箱")
    password: str = Field(..., description="密码")
    
    class Config:
        json_schema_extra = {
            "example": {
                "email": "user@example.com",
                "password": "password123"
            }
        }


class RefreshTokenRequest(BaseModel):
    """刷新Token请求"""
    refresh_token: str = Field(..., description="刷新令牌")
    
    class Config:
        json_schema_extra = {
            "example": {
                "refresh_token": "eyJhbGciOiJIUzI1NiIs..."
            }
        }


# =====================================================
# 响应模型
# =====================================================

class TokenResponse(BaseModel):
    """Token响应"""
    access_token: str = Field(..., description="访问令牌")
    refresh_token: str = Field(..., description="刷新令牌")
    expires_in: int = Field(..., description="Token有效期(秒)")


class UserAuthResponse(BaseModel):
    """用户认证响应"""
    user_id: int = Field(..., description="用户ID")
    email: str = Field(..., description="用户邮箱")
    username: str = Field(..., description="用户名")
    nickname: Optional[str] = Field(None, description="用户昵称")
    avatar_url: Optional[str] = Field(None, description="头像URL")
    subscription_type: str = Field(..., description="订阅类型")
    access_token: str = Field(..., description="访问令牌")
    refresh_token: str = Field(..., description="刷新令牌")
    expires_in: int = Field(..., description="Token有效期(秒)")


class MessageResponse(BaseModel):
    """消息响应"""
    message: str = Field(..., description="操作结果消息")


# =====================================================
# 路由处理函数
# =====================================================

@router.post(
    "/register",
    response_model=ApiResponse[UserAuthResponse],
    status_code=status.HTTP_201_CREATED,
    summary="用户注册",
    description="新用户注册，创建用户账户并返回认证Token"
)
async def register(
    request: RegisterRequest,
    db: AsyncSession = Depends(get_db_session)
):
    """
    用户注册接口
    
    - **email**: 用户邮箱（必填，唯一）
    - **password**: 密码（必填，6-20位）
    - **username**: 用户名（可选，默认为邮箱前缀）
    - **nickname**: 昵称（可选）
    
    注册成功返回用户信息和认证Token
    """
    auth_service = AuthService(db)
    
    result, error_code, error_detail = await auth_service.register(
        email=request.email,
        password=request.password,
        username=request.username,
        nickname=request.nickname
    )
    
    if error_code:
        raise HTTPException(
            status_code=400,
            detail=error_response(
                code=error_code,
                detail=error_detail
            )
        )
    
    return created_response(data=result, message="注册成功")


@router.post(
    "/login",
    response_model=ApiResponse[UserAuthResponse],
    summary="用户登录",
    description="用户登录，验证邮箱和密码，返回认证Token"
)
async def login(
    request: LoginRequest,
    db: AsyncSession = Depends(get_db_session)
):
    """
    用户登录接口
    
    - **email**: 用户邮箱（必填）
    - **password**: 密码（必填）
    
    登录成功返回用户信息和认证Token
    """
    auth_service = AuthService(db)
    
    result, error_code, error_detail = await auth_service.login(
        email=request.email,
        password=request.password
    )
    
    if error_code:
        raise HTTPException(
            status_code=401,
            detail=error_response(
                code=error_code,
                detail=error_detail
            )
        )
    
    return success_response(data=result, message="登录成功")


@router.post(
    "/logout",
    response_model=ApiResponse[MessageResponse],
    summary="用户登出",
    description="用户登出，撤销当前Token"
)
async def logout(
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
):
    """
    用户登出接口
    
    需要认证，登出后当前Token将失效
    """
    # TODO: 实现Token撤销逻辑
    return success_response(data={"message": "登出成功"})


@router.post(
    "/refresh",
    response_model=ApiResponse[TokenResponse],
    summary="刷新Token",
    description="使用Refresh Token获取新的Access Token"
)
async def refresh_token(
    request: RefreshTokenRequest,
    db: AsyncSession = Depends(get_db_session)
):
    """
    刷新Token接口
    
    - **refresh_token**: 刷新令牌（必填）
    
    使用有效的Refresh Token获取新的Access Token和Refresh Token
    """
    auth_service = AuthService(db)
    
    result, error_code, error_detail = await auth_service.refresh_token(
        refresh_token=request.refresh_token
    )
    
    if error_code:
        raise HTTPException(
            status_code=401,
            detail=error_response(
                code=error_code,
                detail=error_detail
            )
        )
    
    return success_response(data=result, message="Token刷新成功")


@router.get(
    "/me",
    response_model=ApiResponse[dict],
    summary="获取当前用户信息",
    description="获取当前登录用户的详细信息"
)
async def get_me(current_user: dict = Depends(get_current_user)):
    """
    获取当前用户信息
    
    需要认证，返回当前登录用户的详细信息
    """
    return success_response(data=current_user)
