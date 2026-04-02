# -*- coding: utf-8 -*-
"""
深觅 AI Coach - 安全工具模块

该模块提供：
- 密码哈希（bcrypt）
- JWT Token生成与验证
- Token刷新机制
"""

import uuid
from datetime import datetime, timedelta
from typing import Optional, Dict, Any

import bcrypt
from jose import JWTError, jwt

from settings import settings


# =====================================================
# 密码相关函数
# =====================================================

def hash_password(password: str) -> str:
    """
    对密码进行bcrypt哈希
    
    bcrypt 限制密码长度不能超过 72 字节
    
    Args:
        password: 明文密码
        
    Returns:
        str: 密码哈希值
    """
    # bcrypt 限制密码长度不能超过 72 字节
    password_bytes = password.encode('utf-8')
    if len(password_bytes) > 72:
        password_bytes = password_bytes[:72]
    
    # 生成salt并哈希
    salt = bcrypt.gensalt(rounds=settings.BCRYPT_ROUNDS)
    hashed = bcrypt.hashpw(password_bytes, salt)
    return hashed.decode('utf-8')


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    验证密码
    
    bcrypt 限制密码长度不能超过 72 字节
    
    Args:
        plain_password: 明文密码
        hashed_password: 密码哈希值
        
    Returns:
        bool: 密码正确返回True
    """
    # bcrypt 限制密码长度不能超过 72 字节
    password_bytes = plain_password.encode('utf-8')
    if len(password_bytes) > 72:
        password_bytes = password_bytes[:72]
    
    hashed_bytes = hashed_password.encode('utf-8')
    return bcrypt.checkpw(password_bytes, hashed_bytes)


# =====================================================
# Token相关函数
# =====================================================

def generate_token_id() -> str:
    """
    生成唯一Token ID
    
    Returns:
        str: UUID格式的Token ID
    """
    return str(uuid.uuid4())


def create_access_token(
    data: Dict[str, Any],
    expires_delta: Optional[timedelta] = None
) -> str:
    """
    创建Access Token
    
    Args:
        data: 要编码到Token中的数据
        expires_delta: 过期时间增量，默认使用配置值
        
    Returns:
        str: JWT Token字符串
    """
    to_encode = data.copy()
    
    # 计算过期时间
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(
            minutes=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES
        )
    
    # 添加标准声明
    to_encode.update({
        "exp": expire,
        "iat": datetime.utcnow(),
        "type": "access",
        "jti": generate_token_id()
    })
    
    # 编码JWT
    encoded_jwt = jwt.encode(
        to_encode,
        settings.JWT_SECRET_KEY,
        algorithm=settings.JWT_ALGORITHM
    )
    
    return encoded_jwt


def create_refresh_token(
    data: Dict[str, Any],
    expires_delta: Optional[timedelta] = None
) -> str:
    """
    创建Refresh Token
    
    Args:
        data: 要编码到Token中的数据
        expires_delta: 过期时间增量，默认使用配置值
        
    Returns:
        str: JWT Token字符串
    """
    to_encode = data.copy()
    
    # 计算过期时间
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(
            days=settings.JWT_REFRESH_TOKEN_EXPIRE_DAYS
        )
    
    # 添加标准声明
    to_encode.update({
        "exp": expire,
        "iat": datetime.utcnow(),
        "type": "refresh",
        "jti": generate_token_id()
    })
    
    # 编码JWT
    encoded_jwt = jwt.encode(
        to_encode,
        settings.JWT_SECRET_KEY,
        algorithm=settings.JWT_ALGORITHM
    )
    
    return encoded_jwt


def decode_token(token: str) -> Optional[Dict[str, Any]]:
    """
    解码并验证JWT Token
    
    Args:
        token: JWT Token字符串
        
    Returns:
        Optional[Dict]: Token载荷数据，验证失败返回None
    """
    try:
        payload = jwt.decode(
            token,
            settings.JWT_SECRET_KEY,
            algorithms=[settings.JWT_ALGORITHM]
        )
        return payload
    except JWTError:
        return None


def verify_token_type(token: str, expected_type: str) -> Optional[Dict[str, Any]]:
    """
    验证Token类型
    
    Args:
        token: JWT Token字符串
        expected_type: 期望的Token类型 (access/refresh)
        
    Returns:
        Optional[Dict]: 验证通过的Token载荷，失败返回None
    """
    payload = decode_token(token)
    
    if payload is None:
        return None
    
    token_type = payload.get("type")
    if token_type != expected_type:
        return None
    
    return payload


def get_token_expiry(token: str) -> Optional[datetime]:
    """
    获取Token过期时间
    
    Args:
        token: JWT Token字符串
        
    Returns:
        Optional[datetime]: 过期时间，解析失败返回None
    """
    payload = decode_token(token)
    
    if payload is None:
        return None
    
    exp_timestamp = payload.get("exp")
    if exp_timestamp:
        return datetime.utcfromtimestamp(exp_timestamp)
    
    return None


def is_token_expired(token: str) -> bool:
    """
    检查Token是否已过期
    
    Args:
        token: JWT Token字符串
        
    Returns:
        bool: 已过期返回True
    """
    expiry = get_token_expiry(token)
    
    if expiry is None:
        return True
    
    return datetime.utcnow() >= expiry


# =====================================================
# Token数据提取函数
# =====================================================

def get_user_id_from_token(token: str) -> Optional[int]:
    """
    从Token中提取用户ID
    
    Args:
        token: JWT Token字符串
        
    Returns:
        Optional[int]: 用户ID，提取失败返回None
    """
    payload = decode_token(token)
    
    if payload is None:
        return None
    
    user_id = payload.get("sub")
    if user_id:
        try:
            return int(user_id)
        except (ValueError, TypeError):
            return None
    
    return None


def get_token_data(token: str) -> Dict[str, Any]:
    """
    获取Token中的所有数据
    
    Args:
        token: JWT Token字符串
        
    Returns:
        Dict: Token数据字典，失败返回空字典
    """
    payload = decode_token(token)
    return payload or {}
