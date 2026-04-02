# -*- coding: utf-8 -*-
"""
深觅 AI Coach - 数据库模块

该模块提供数据库连接、模型定义和会话管理功能
"""

from database.connection import (
    engine,
    async_session,
    init_db,
    get_db,
    close_db,
)
from database.models import (
    Base,
    User,
    UserProfile,
    UserToken,
    Conversation,
    Message,
    ConversationSummary,
    Assessment,
    AssessmentResult,
    AssessmentResponse,
    Goal,
    GoalMilestone,
    GoalProgress,
    Subscription,
    Payment,
    UsageQuota,
    StrengthDefinition,
    CoachPrompt,
    SystemConfig,
    AuditLog,
    AppLog,
    Notification,
)

__all__ = [
    # 连接相关
    "engine",
    "async_session",
    "init_db",
    "get_db",
    "close_db",
    # 模型相关
    "Base",
    "User",
    "UserProfile",
    "UserToken",
    "Conversation",
    "Message",
    "ConversationSummary",
    "Assessment",
    "AssessmentResult",
    "AssessmentResponse",
    "Goal",
    "GoalMilestone",
    "GoalProgress",
    "Subscription",
    "Payment",
    "UsageQuota",
    "StrengthDefinition",
    "CoachPrompt",
    "SystemConfig",
    "AuditLog",
    "AppLog",
    "Notification",
]
