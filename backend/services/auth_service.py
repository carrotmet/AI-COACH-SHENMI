# -*- coding: utf-8 -*-
"""
深觅 AI Coach - 认证服务模块

该模块提供用户认证相关的业务逻辑：
- 用户注册
- 用户登录
- Token管理
- 用户验证
"""

from datetime import datetime, timedelta
from typing import Optional, Tuple, Dict, Any

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_

from database.models import (
    User,
    UserProfile,
    UserToken,
    UsageQuota,
    SubscriptionType,
    TokenType,
    UserStatus,
)
from utils.security import (
    hash_password,
    verify_password,
    create_access_token,
    create_refresh_token,
    decode_token,
    get_user_id_from_token,
)
from utils.response import ResponseCode
from settings import settings


class AuthService:
    """
    认证服务类
    
    处理用户认证相关的所有业务逻辑
    """
    
    def __init__(self, db: AsyncSession):
        """
        初始化认证服务
        
        Args:
            db: 数据库会话
        """
        self.db = db
    
    # =====================================================
    # 用户注册
    # =====================================================
    
    async def register(
        self,
        email: str,
        password: str,
        username: Optional[str] = None,
        nickname: Optional[str] = None
    ) -> Tuple[Optional[Dict[str, Any]], Optional[ResponseCode], Optional[str]]:
        """
        用户注册
        
        Args:
            email: 用户邮箱
            password: 用户密码
            username: 用户名（可选，默认为邮箱前缀）
            nickname: 用户昵称（可选）
            
        Returns:
            Tuple: (用户数据, 错误码, 错误详情)
            - 成功: (用户数据字典, None, None)
            - 失败: (None, 错误码, 错误详情)
        """
        # 检查邮箱是否已存在
        existing_user = await self._get_user_by_email(email)
        if existing_user:
            return None, ResponseCode.USER_ALREADY_EXISTS, "该邮箱已被注册"
        
        # 生成用户名
        if not username:
            username = email.split("@")[0]
        
        # 确保用户名唯一
        base_username = username
        counter = 1
        while await self._get_user_by_username(username):
            username = f"{base_username}_{counter}"
            counter += 1
        
        # 创建用户
        user = User(
            username=username,
            email=email,
            password_hash=hash_password(password),
            status=UserStatus.ACTIVE.value,
            subscription_type=SubscriptionType.FREE.value,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )
        
        self.db.add(user)
        await self.db.flush()  # 获取user.id
        
        # 创建用户画像
        profile = UserProfile(
            user_id=user.id,
            nickname=nickname or username,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )
        self.db.add(profile)
        
        # 创建使用配额
        quota = UsageQuota(
            user_id=user.id,
            plan_type=SubscriptionType.FREE.value,
            conversation_limit=settings.DEFAULT_CONVERSATION_LIMIT,
            message_limit=settings.DEFAULT_MESSAGE_LIMIT,
            assessment_limit=settings.DEFAULT_ASSESSMENT_LIMIT,
            ai_call_limit=settings.DEFAULT_AI_CALL_LIMIT,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )
        self.db.add(quota)
        
        await self.db.commit()
        
        # 生成Token
        access_token = create_access_token({"sub": str(user.id)})
        refresh_token = create_refresh_token({"sub": str(user.id)})
        
        # 保存Token到数据库
        await self._save_token(user.id, TokenType.ACCESS.value, access_token)
        await self._save_token(user.id, TokenType.REFRESH.value, refresh_token)
        
        return {
            "user_id": user.id,
            "email": user.email,
            "username": user.username,
            "nickname": profile.nickname,
            "subscription_type": user.subscription_type,
            "created_at": user.created_at.isoformat(),
            "access_token": access_token,
            "refresh_token": refresh_token,
            "expires_in": settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES * 60
        }, None, None
    
    # =====================================================
    # 用户登录
    # =====================================================
    
    async def login(
        self,
        email: str,
        password: str
    ) -> Tuple[Optional[Dict[str, Any]], Optional[ResponseCode], Optional[str]]:
        """
        用户登录
        
        Args:
            email: 用户邮箱
            password: 用户密码
            
        Returns:
            Tuple: (用户数据, 错误码, 错误详情)
        """
        # 查找用户
        user = await self._get_user_by_email(email)
        
        if not user:
            return None, ResponseCode.USER_NOT_FOUND, "该邮箱未注册"
        
        # 检查用户状态
        if user.status == UserStatus.INACTIVE.value:
            return None, ResponseCode.USER_INACTIVE, "用户未激活"
        
        if user.status == UserStatus.SUSPENDED.value:
            return None, ResponseCode.USER_SUSPENDED, "用户已被暂停"
        
        if user.status == UserStatus.DELETED.value:
            return None, ResponseCode.USER_DELETED, "用户已删除"
        
        # 验证密码
        if not verify_password(password, user.password_hash):
            return None, ResponseCode.INVALID_CREDENTIALS, "密码不正确"
        
        # 更新最后登录时间
        user.last_login_at = datetime.utcnow()
        await self.db.commit()
        
        # 获取用户画像
        profile = await self._get_user_profile(user.id)
        
        # 生成Token
        access_token = create_access_token({"sub": str(user.id)})
        refresh_token = create_refresh_token({"sub": str(user.id)})
        
        # 保存Token到数据库
        await self._save_token(user.id, TokenType.ACCESS.value, access_token)
        await self._save_token(user.id, TokenType.REFRESH.value, refresh_token)
        
        return {
            "user_id": user.id,
            "email": user.email,
            "username": user.username,
            "nickname": profile.nickname if profile else user.username,
            "avatar_url": user.avatar_url,
            "subscription_type": user.subscription_type,
            "access_token": access_token,
            "refresh_token": refresh_token,
            "expires_in": settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES * 60
        }, None, None
    
    # =====================================================
    # Token刷新
    # =====================================================
    
    async def refresh_token(
        self,
        refresh_token: str
    ) -> Tuple[Optional[Dict[str, Any]], Optional[ResponseCode], Optional[str]]:
        """
        刷新Access Token
        
        Args:
            refresh_token: 刷新令牌
            
        Returns:
            Tuple: (Token数据, 错误码, 错误详情)
        """
        # 验证Refresh Token
        payload = decode_token(refresh_token)
        
        if payload is None:
            return None, ResponseCode.INVALID_REFRESH_TOKEN, "Refresh Token无效"
        
        # 检查Token类型
        token_type = payload.get("type")
        if token_type != "refresh":
            return None, ResponseCode.INVALID_REFRESH_TOKEN, "无效的Refresh Token"
        
        # 获取用户ID
        user_id = payload.get("sub")
        if not user_id:
            return None, ResponseCode.INVALID_REFRESH_TOKEN, "Refresh Token数据无效"
        
        # 检查用户是否存在
        user = await self._get_user_by_id(int(user_id))
        if not user:
            return None, ResponseCode.USER_NOT_FOUND, "用户不存在"
        
        # 检查用户状态
        if user.status != UserStatus.ACTIVE.value:
            return None, ResponseCode.USER_INACTIVE, "用户状态异常"
        
        # 生成新的Token
        new_access_token = create_access_token({"sub": str(user.id)})
        new_refresh_token = create_refresh_token({"sub": str(user.id)})
        
        # 保存新Token到数据库
        await self._save_token(user.id, TokenType.ACCESS.value, new_access_token)
        await self._save_token(user.id, TokenType.REFRESH.value, new_refresh_token)
        
        return {
            "access_token": new_access_token,
            "refresh_token": new_refresh_token,
            "expires_in": settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES * 60
        }, None, None
    
    # =====================================================
    # 用户登出
    # =====================================================
    
    async def logout(self, user_id: int, token: str) -> bool:
        """
        用户登出
        
        撤销用户的Token
        
        Args:
            user_id: 用户ID
            token: 当前Token
            
        Returns:
            bool: 登出成功返回True
        """
        try:
            # 撤销当前Token
            result = await self.db.execute(
                select(UserToken).where(
                    and_(
                        UserToken.user_id == user_id,
                        UserToken.token_hash == token,
                        UserToken.revoked == False
                    )
                )
            )
            user_token = result.scalar_one_or_none()
            
            if user_token:
                user_token.revoked = True
                await self.db.commit()
            
            return True
        except Exception:
            return False
    
    # =====================================================
    # 辅助方法
    # =====================================================
    
    async def _get_user_by_email(self, email: str) -> Optional[User]:
        """通过邮箱获取用户"""
        result = await self.db.execute(
            select(User).where(User.email == email)
        )
        return result.scalar_one_or_none()
    
    async def _get_user_by_username(self, username: str) -> Optional[User]:
        """通过用户名获取用户"""
        result = await self.db.execute(
            select(User).where(User.username == username)
        )
        return result.scalar_one_or_none()
    
    async def _get_user_by_id(self, user_id: int) -> Optional[User]:
        """通过ID获取用户"""
        result = await self.db.execute(
            select(User).where(User.id == user_id)
        )
        return result.scalar_one_or_none()
    
    async def _get_user_profile(self, user_id: int) -> Optional[UserProfile]:
        """获取用户画像"""
        result = await self.db.execute(
            select(UserProfile).where(UserProfile.user_id == user_id)
        )
        return result.scalar_one_or_none()
    
    async def _save_token(
        self,
        user_id: int,
        token_type: str,
        token: str
    ) -> None:
        """保存Token到数据库"""
        # 计算过期时间
        if token_type == TokenType.ACCESS.value:
            expires_at = datetime.utcnow() + timedelta(
                minutes=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES
            )
        else:
            expires_at = datetime.utcnow() + timedelta(
                days=settings.JWT_REFRESH_TOKEN_EXPIRE_DAYS
            )
        
        user_token = UserToken(
            user_id=user_id,
            token_type=token_type,
            token_hash=token,
            expires_at=expires_at,
            created_at=datetime.utcnow(),
            revoked=False
        )
        
        self.db.add(user_token)
        await self.db.commit()
    
    async def verify_token(self, token: str) -> Tuple[Optional[int], Optional[ResponseCode]]:
        """
        验证Token
        
        Args:
            token: JWT Token
            
        Returns:
            Tuple: (用户ID, 错误码)
        """
        # 解码Token
        payload = decode_token(token)
        
        if payload is None:
            return None, ResponseCode.INVALID_TOKEN
        
        # 检查Token类型
        token_type = payload.get("type")
        if token_type != "access":
            return None, ResponseCode.INVALID_TOKEN
        
        # 获取用户ID
        user_id = payload.get("sub")
        if not user_id:
            return None, ResponseCode.INVALID_TOKEN
        
        # 检查用户是否存在
        user = await self._get_user_by_id(int(user_id))
        if not user:
            return None, ResponseCode.USER_NOT_FOUND
        
        # 检查用户状态
        if user.status != UserStatus.ACTIVE.value:
            return None, ResponseCode.USER_INACTIVE
        
        return int(user_id), None
