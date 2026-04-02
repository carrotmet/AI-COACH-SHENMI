# -*- coding: utf-8 -*-
"""
深觅 AI Coach - 配置管理模块

该模块负责管理应用程序的所有配置，包括：
- 环境变量配置
- 数据库配置
- JWT配置
- 日志配置
"""

import os
from typing import Optional, List
from functools import lru_cache
from pydantic_settings import BaseSettings
from pydantic import Field


class Settings(BaseSettings):
    """
    应用程序配置类
    
    使用Pydantic Settings管理环境变量和配置
    支持从.env文件加载配置
    """
    
    # =====================================================
    # 应用基础配置
    # =====================================================
    APP_NAME: str = Field(default="深觅 AI Coach", description="应用名称")
    APP_VERSION: str = Field(default="1.0.0", description="应用版本")
    APP_DESCRIPTION: str = Field(
        default="基于AI的个人优势教练平台",
        description="应用描述"
    )
    APP_ENV: str = Field(default="development", description="运行环境")
    DEBUG: bool = Field(default=False, description="调试模式")
    
    # 服务器配置
    HOST: str = Field(default="0.0.0.0", description="服务器主机")
    PORT: int = Field(default=8080, description="服务器端口")
    
    # =====================================================
    # 数据库配置
    # =====================================================
    DATABASE_URL: str = Field(
        default="sqlite+aiosqlite:///./ai_coach.db",
        description="数据库连接URL"
    )
    DATABASE_ECHO: bool = Field(
        default=False,
        description="是否打印SQL语句"
    )
    DATABASE_POOL_SIZE: int = Field(
        default=10,
        description="数据库连接池大小"
    )
    
    # =====================================================
    # JWT认证配置
    # =====================================================
    JWT_SECRET_KEY: str = Field(
        default="your-secret-key-change-in-production",
        description="JWT密钥（生产环境必须修改）"
    )
    JWT_ALGORITHM: str = Field(default="HS256", description="JWT算法")
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(
        default=15,
        description="Access Token过期时间（分钟）"
    )
    JWT_REFRESH_TOKEN_EXPIRE_DAYS: int = Field(
        default=7,
        description="Refresh Token过期时间（天）"
    )
    
    # =====================================================
    # 密码安全配置
    # =====================================================
    PASSWORD_MIN_LENGTH: int = Field(
        default=6,
        description="密码最小长度"
    )
    PASSWORD_MAX_LENGTH: int = Field(
        default=20,
        description="密码最大长度"
    )
    BCRYPT_ROUNDS: int = Field(
        default=12,
        description="bcrypt加密轮数"
    )
    
    # =====================================================
    # CORS配置
    # =====================================================
    CORS_ORIGINS: List[str] = Field(
        default=["*"],
        description="允许的跨域来源"
    )
    CORS_ALLOW_CREDENTIALS: bool = Field(
        default=True,
        description="允许跨域携带凭证"
    )
    CORS_ALLOW_METHODS: List[str] = Field(
        default=["*"],
        description="允许的HTTP方法"
    )
    CORS_ALLOW_HEADERS: List[str] = Field(
        default=["*"],
        description="允许的HTTP头"
    )
    
    # =====================================================
    # 日志配置
    # =====================================================
    LOG_LEVEL: str = Field(default="INFO", description="日志级别")
    LOG_FORMAT: str = Field(
        default="json",
        description="日志格式: json/text"
    )
    LOG_FILE: Optional[str] = Field(
        default=None,
        description="日志文件路径"
    )
    
    # =====================================================
    # 业务配置
    # =====================================================
    # 订阅配置
    DEFAULT_PLAN_TYPE: str = Field(
        default="free",
        description="默认订阅类型"
    )
    
    # 配额配置
    DEFAULT_CONVERSATION_LIMIT: int = Field(
        default=10,
        description="默认对话限制"
    )
    DEFAULT_MESSAGE_LIMIT: int = Field(
        default=100,
        description="默认消息限制"
    )
    DEFAULT_ASSESSMENT_LIMIT: int = Field(
        default=1,
        description="默认评估限制"
    )
    DEFAULT_AI_CALL_LIMIT: int = Field(
        default=100,
        description="默认AI调用限制"
    )
    
    # 会话配置
    SESSION_TIMEOUT_HOURS: int = Field(
        default=24,
        description="会话超时时间（小时）"
    )
    MAX_CONVERSATION_LENGTH: int = Field(
        default=100,
        description="单对话最大消息数"
    )
    MAX_MESSAGE_LENGTH: int = Field(
        default=4000,
        description="单消息最大字符数"
    )
    
    # =====================================================
    # API配置
    # =====================================================
    API_V1_PREFIX: str = Field(
        default="/api/v1",
        description="API版本1前缀"
    )
    API_TITLE: str = Field(
        default="深觅 AI Coach API",
        description="API文档标题"
    )
    
    # =====================================================
    # AI服务配置
    # =====================================================
    # Kimi (Moonshot) API配置 - 国内首选
    KIMI_API_KEY: Optional[str] = Field(
        default=None,
        description="Kimi (Moonshot) API密钥"
    )
    KIMI_BASE_URL: str = Field(
        default="https://api.moonshot.cn/v1",
        description="Kimi API基础URL"
    )
    KIMI_MODEL: str = Field(
        default="kimi-k2-turbo-preview",
        description="Kimi模型名称"
    )
    
    # OpenAI API配置（国际备用）
    OPENAI_API_KEY: Optional[str] = Field(
        default=None,
        description="OpenAI API密钥"
    )
    OPENAI_BASE_URL: str = Field(
        default="https://api.openai.com/v1",
        description="OpenAI API基础URL"
    )
    LLM_MODEL: str = Field(
        default="gpt-4o-mini",
        description="使用的LLM模型"
    )
    LLM_TEMPERATURE: float = Field(
        default=0.7,
        description="LLM温度参数"
    )
    LLM_MAX_TOKENS: int = Field(
        default=2000,
        description="最大Token数"
    )
    ANTHROPIC_API_KEY: Optional[str] = Field(
        default=None,
        description="Anthropic API密钥"
    )
    
    # =====================================================
    # 对话限制配置
    # =====================================================
    FREE_DAILY_CHAT_LIMIT: int = Field(
        default=3,
        description="免费用户每日对话次数限制"
    )
    BASIC_DAILY_CHAT_LIMIT: int = Field(
        default=20,
        description="基础版用户每日对话次数限制"
    )
    PRO_DAILY_CHAT_LIMIT: int = Field(
        default=-1,
        description="专业版用户每日对话次数限制"
    )
    
    # =====================================================
    # Redis配置
    # =====================================================
    USE_REDIS: bool = Field(
        default=False,
        description="是否启用Redis"
    )
    REDIS_URL: Optional[str] = Field(
        default=None,
        description="Redis连接URL"
    )
    
    class Config:
        """Pydantic配置"""
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True


@lru_cache()
def get_settings() -> Settings:
    """
    获取配置实例（单例模式）
    
    使用lru_cache确保配置只被加载一次
    
    Returns:
        Settings: 配置实例
    """
    return Settings()


# 全局配置实例
settings = get_settings()
