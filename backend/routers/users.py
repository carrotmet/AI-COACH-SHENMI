# -*- coding: utf-8 -*-
"""
深觅 AI Coach - 用户路由模块

该模块提供用户管理相关的API接口：
- GET /users/me - 获取当前用户信息
- PUT /users/me - 更新用户信息
- GET /users/me/profile - 获取用户画像
- PUT /users/me/profile - 更新用户画像
"""

from typing import Optional, List
from datetime import date

from fastapi import APIRouter, Depends, HTTPException, status, Query
from pydantic import BaseModel, Field, EmailStr
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc

from database.connection import get_db_session
from database.models import (
    User,
    UserProfile,
    Assessment,
    Conversation,
    SubscriptionType,
)
from middleware.auth_middleware import get_current_user
from utils.response import (
    success_response,
    error_response,
    paginated_response,
    ResponseCode,
    ApiResponse,
)


# =====================================================
# 路由定义
# =====================================================
router = APIRouter(
    tags=["用户管理"],
    dependencies=[Depends(get_current_user)],
    responses={
        401: {"description": "未授权"},
        403: {"description": "无权限"},
    }
)


# =====================================================
# 请求模型
# =====================================================

class UpdateUserRequest(BaseModel):
    """更新用户信息请求"""
    nickname: Optional[str] = Field(None, description="用户昵称")
    avatar_url: Optional[str] = Field(None, description="头像URL")
    
    class Config:
        json_schema_extra = {
            "example": {
                "nickname": "新昵称",
                "avatar_url": "https://example.com/avatar.jpg"
            }
        }


class UpdateProfileRequest(BaseModel):
    """更新用户画像请求"""
    nickname: Optional[str] = Field(None, description="昵称")
    gender: Optional[str] = Field(None, description="性别")
    birth_date: Optional[date] = Field(None, description="出生日期")
    occupation: Optional[str] = Field(None, description="职业")
    company: Optional[str] = Field(None, description="公司")
    industry: Optional[str] = Field(None, description="行业")
    location: Optional[str] = Field(None, description="所在地")
    bio: Optional[str] = Field(None, description="个人简介")
    goals: Optional[str] = Field(None, description="用户目标")
    interests: Optional[str] = Field(None, description="兴趣爱好")
    coaching_style_preference: Optional[str] = Field(None, description="教练风格偏好")
    
    class Config:
        json_schema_extra = {
            "example": {
                "nickname": "小明",
                "gender": "male",
                "occupation": "软件工程师",
                "industry": "互联网",
                "bio": "热爱技术，追求成长"
            }
        }


class ChangePasswordRequest(BaseModel):
    """修改密码请求"""
    old_password: str = Field(..., min_length=6, description="旧密码")
    new_password: str = Field(..., min_length=6, max_length=20, description="新密码")
    
    class Config:
        json_schema_extra = {
            "example": {
                "old_password": "oldpass123",
                "new_password": "newpass456"
            }
        }


# =====================================================
# 响应模型
# =====================================================

class UserInfoResponse(BaseModel):
    """用户信息响应"""
    user_id: int = Field(..., description="用户ID")
    email: str = Field(..., description="用户邮箱")
    username: str = Field(..., description="用户名")
    nickname: Optional[str] = Field(None, description="昵称")
    avatar_url: Optional[str] = Field(None, description="头像URL")
    subscription_type: str = Field(..., description="订阅类型")
    created_at: str = Field(..., description="注册时间")


class UserProfileResponse(BaseModel):
    """用户画像响应"""
    user_id: int = Field(..., description="用户ID")
    nickname: Optional[str] = Field(None, description="昵称")
    gender: Optional[str] = Field(None, description="性别")
    birth_date: Optional[str] = Field(None, description="出生日期")
    occupation: Optional[str] = Field(None, description="职业")
    company: Optional[str] = Field(None, description="公司")
    industry: Optional[str] = Field(None, description="行业")
    location: Optional[str] = Field(None, description="所在地")
    bio: Optional[str] = Field(None, description="个人简介")
    goals: Optional[str] = Field(None, description="目标")
    interests: Optional[str] = Field(None, description="兴趣爱好")
    personality_type: Optional[str] = Field(None, description="性格类型")
    coaching_style_preference: Optional[str] = Field(None, description="教练风格偏好")


class SubscriptionInfo(BaseModel):
    """订阅信息"""
    type: str = Field(..., description="订阅类型")
    expires_at: Optional[str] = Field(None, description="过期时间")


class UsageStats(BaseModel):
    """使用统计"""
    total_assessments: int = Field(..., description="总测评数")
    total_conversations: int = Field(..., description="总对话数")
    last_active: Optional[str] = Field(None, description="最后活跃时间")


class UserDetailResponse(BaseModel):
    """用户详情响应"""
    user_id: int = Field(..., description="用户ID")
    email: str = Field(..., description="用户邮箱")
    nickname: Optional[str] = Field(None, description="昵称")
    avatar: Optional[str] = Field(None, description="头像URL")
    created_at: str = Field(..., description="注册时间")
    subscription: SubscriptionInfo = Field(..., description="订阅信息")
    usage_stats: UsageStats = Field(..., description="使用统计")


class AssessmentHistoryItem(BaseModel):
    """测评历史项"""
    assessment_id: int = Field(..., description="测评ID")
    type: str = Field(..., description="测评类型")
    status: str = Field(..., description="状态")
    score: Optional[float] = Field(None, description="得分")
    created_at: str = Field(..., description="创建时间")
    completed_at: Optional[str] = Field(None, description="完成时间")


class ConversationHistoryItem(BaseModel):
    """对话历史项"""
    conversation_id: int = Field(..., description="对话ID")
    title: str = Field(..., description="对话标题")
    message_count: int = Field(..., description="消息数量")
    created_at: str = Field(..., description="创建时间")
    updated_at: str = Field(..., description="更新时间")


class MessageResponse(BaseModel):
    """消息响应"""
    message: str = Field(..., description="操作结果消息")


# =====================================================
# 路由处理函数
# =====================================================

@router.get(
    "/me",
    response_model=ApiResponse[UserDetailResponse],
    summary="获取当前用户信息",
    description="获取当前登录用户的详细信息和统计数据"
)
async def get_current_user_info(
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
):
    """
    获取当前用户信息
    
    返回用户的详细信息、订阅状态和使用统计
    """
    user_id = current_user["id"]
    
    # 获取用户详细信息
    result = await db.execute(
        select(User).where(User.id == user_id)
    )
    user = result.scalar_one()
    
    # 获取用户画像
    profile_result = await db.execute(
        select(UserProfile).where(UserProfile.user_id == user_id)
    )
    profile = profile_result.scalar_one_or_none()
    
    # 获取测评数量
    assessment_result = await db.execute(
        select(Assessment).where(Assessment.user_id == user_id)
    )
    assessments = assessment_result.scalars().all()
    
    # 获取对话数量
    conversation_result = await db.execute(
        select(Conversation).where(Conversation.user_id == user_id)
    )
    conversations = conversation_result.scalars().all()
    
    return success_response(
        data={
            "user_id": user.id,
            "email": user.email,
            "nickname": profile.nickname if profile else user.username,
            "avatar": user.avatar_url,
            "created_at": user.created_at.isoformat() if user.created_at else None,
            "subscription": {
                "type": user.subscription_type,
                "expires_at": None  # TODO: 从订阅表获取
            },
            "usage_stats": {
                "total_assessments": len(assessments),
                "total_conversations": len(conversations),
                "last_active": user.last_login_at.isoformat() if user.last_login_at else None
            }
        }
    )


@router.put(
    "/me",
    response_model=ApiResponse[UserInfoResponse],
    summary="更新用户信息",
    description="更新当前用户的基本信息"
)
async def update_user_info(
    request: UpdateUserRequest,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
):
    """
    更新用户信息
    
    - **nickname**: 昵称（可选）
    - **avatar_url**: 头像URL（可选）
    """
    user_id = current_user["id"]
    
    # 获取用户
    result = await db.execute(
        select(User).where(User.id == user_id)
    )
    user = result.scalar_one()
    
    # 获取用户画像
    profile_result = await db.execute(
        select(UserProfile).where(UserProfile.user_id == user_id)
    )
    profile = profile_result.scalar_one_or_none()
    
    # 更新用户信息
    if request.avatar_url is not None:
        user.avatar_url = request.avatar_url
    
    # 更新用户画像
    if profile and request.nickname is not None:
        profile.nickname = request.nickname
    
    await db.commit()
    
    return success_response(
        data={
            "user_id": user.id,
            "email": user.email,
            "username": user.username,
            "nickname": profile.nickname if profile else user.username,
            "avatar_url": user.avatar_url,
            "subscription_type": user.subscription_type,
            "created_at": user.created_at.isoformat() if user.created_at else None
        },
        message="用户信息更新成功"
    )


@router.get(
    "/me/profile",
    response_model=ApiResponse[UserProfileResponse],
    summary="获取用户画像",
    description="获取当前用户的详细画像信息"
)
async def get_user_profile(
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
):
    """
    获取用户画像
    
    返回用户的详细画像信息，包括个人资料、职业信息等
    """
    user_id = current_user["id"]
    
    # 获取用户画像
    result = await db.execute(
        select(UserProfile).where(UserProfile.user_id == user_id)
    )
    profile = result.scalar_one_or_none()
    
    if not profile:
        # 如果没有画像，返回空数据
        return success_response(
            data={
                "user_id": user_id,
                "nickname": None,
                "gender": None,
                "birth_date": None,
                "occupation": None,
                "company": None,
                "industry": None,
                "location": None,
                "bio": None,
                "goals": None,
                "interests": None,
                "personality_type": None,
                "coaching_style_preference": None
            }
        )
    
    return success_response(
        data={
            "user_id": user_id,
            "nickname": profile.nickname,
            "gender": profile.gender,
            "birth_date": profile.birth_date.isoformat() if profile.birth_date else None,
            "occupation": profile.occupation,
            "company": profile.company,
            "industry": profile.industry,
            "location": profile.location,
            "bio": profile.bio,
            "goals": profile.goals,
            "interests": profile.interests,
            "personality_type": profile.personality_type,
            "coaching_style_preference": profile.coaching_style_preference
        }
    )


@router.put(
    "/me/profile",
    response_model=ApiResponse[UserProfileResponse],
    summary="更新用户画像",
    description="更新当前用户的画像信息"
)
async def update_user_profile(
    request: UpdateProfileRequest,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
):
    """
    更新用户画像
    
    可以更新用户的各种画像信息
    """
    user_id = current_user["id"]
    
    # 获取或创建用户画像
    result = await db.execute(
        select(UserProfile).where(UserProfile.user_id == user_id)
    )
    profile = result.scalar_one_or_none()
    
    if not profile:
        # 创建新画像
        profile = UserProfile(user_id=user_id)
        db.add(profile)
    
    # 更新字段
    update_fields = [
        "nickname", "gender", "birth_date", "occupation",
        "company", "industry", "location", "bio",
        "goals", "interests", "coaching_style_preference"
    ]
    
    for field in update_fields:
        value = getattr(request, field)
        if value is not None:
            setattr(profile, field, value)
    
    await db.commit()
    await db.refresh(profile)
    
    return success_response(
        data={
            "user_id": user_id,
            "nickname": profile.nickname,
            "gender": profile.gender,
            "birth_date": profile.birth_date.isoformat() if profile.birth_date else None,
            "occupation": profile.occupation,
            "company": profile.company,
            "industry": profile.industry,
            "location": profile.location,
            "bio": profile.bio,
            "goals": profile.goals,
            "interests": profile.interests,
            "personality_type": profile.personality_type,
            "coaching_style_preference": profile.coaching_style_preference
        },
        message="用户画像更新成功"
    )


@router.get(
    "/me/assessments",
    response_model=ApiResponse[dict],
    summary="获取用户测评历史",
    description="获取当前用户的测评历史记录"
)
async def get_user_assessments(
    page: int = Query(1, ge=1, description="页码"),
    limit: int = Query(10, ge=1, le=100, description="每页数量"),
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
):
    """
    获取用户测评历史
    
    - **page**: 页码，默认1
    - **limit**: 每页数量，默认10
    """
    user_id = current_user["id"]
    
    # 获取测评列表
    result = await db.execute(
        select(Assessment)
        .where(Assessment.user_id == user_id)
        .order_by(desc(Assessment.created_at))
        .offset((page - 1) * limit)
        .limit(limit)
    )
    assessments = result.scalars().all()
    
    # 获取总数
    count_result = await db.execute(
        select(Assessment).where(Assessment.user_id == user_id)
    )
    total = len(count_result.scalars().all())
    
    items = [
        {
            "assessment_id": a.id,
            "type": a.assessment_type,
            "status": a.status,
            "score": a.score_summary.get("total") if a.score_summary else None,
            "created_at": a.created_at.isoformat() if a.created_at else None,
            "completed_at": a.completed_at.isoformat() if a.completed_at else None
        }
        for a in assessments
    ]
    
    return paginated_response(
        items=items,
        total=total,
        page=page,
        limit=limit
    )


@router.get(
    "/me/conversations",
    response_model=ApiResponse[dict],
    summary="获取用户对话历史",
    description="获取当前用户的对话历史记录"
)
async def get_user_conversations(
    page: int = Query(1, ge=1, description="页码"),
    limit: int = Query(10, ge=1, le=100, description="每页数量"),
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
):
    """
    获取用户对话历史
    
    - **page**: 页码，默认1
    - **limit**: 每页数量，默认10
    """
    user_id = current_user["id"]
    
    # 获取对话列表
    result = await db.execute(
        select(Conversation)
        .where(Conversation.user_id == user_id)
        .order_by(desc(Conversation.updated_at))
        .offset((page - 1) * limit)
        .limit(limit)
    )
    conversations = result.scalars().all()
    
    # 获取总数
    count_result = await db.execute(
        select(Conversation).where(Conversation.user_id == user_id)
    )
    total = len(count_result.scalars().all())
    
    items = [
        {
            "conversation_id": c.id,
            "title": c.title,
            "message_count": c.message_count,
            "created_at": c.created_at.isoformat() if c.created_at else None,
            "updated_at": c.updated_at.isoformat() if c.updated_at else None
        }
        for c in conversations
    ]
    
    return paginated_response(
        items=items,
        total=total,
        page=page,
        limit=limit
    )


@router.put(
    "/me/password",
    response_model=ApiResponse[MessageResponse],
    summary="修改密码",
    description="修改当前用户的密码"
)
async def change_password(
    request: ChangePasswordRequest,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
):
    """
    修改密码
    
    - **old_password**: 旧密码（必填）
    - **new_password**: 新密码（必填，6-20位）
    """
    from utils.security import verify_password, hash_password
    
    user_id = current_user["id"]
    
    # 获取用户
    result = await db.execute(
        select(User).where(User.id == user_id)
    )
    user = result.scalar_one()
    
    # 验证旧密码
    if not verify_password(request.old_password, user.password_hash):
        raise HTTPException(
            status_code=400,
            detail=error_response(
                code=ResponseCode.PASSWORD_INCORRECT,
                detail="旧密码不正确"
            )
        )
    
    # 更新密码
    user.password_hash = hash_password(request.new_password)
    await db.commit()
    
    return success_response(
        data={"message": "密码修改成功"}
    )
