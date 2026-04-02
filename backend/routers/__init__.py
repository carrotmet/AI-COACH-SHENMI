# -*- coding: utf-8 -*-
"""
深觅 AI Coach - API路由模块

包含所有API路由定义
"""

from routers.assessments import router as assessments_router
from routers.conversations import router as conversations_router
from routers.auth import router as auth_router
from routers.users import router as users_router
from routers.subscriptions import router as subscriptions_router
from routers.star import router as star_router
from routers.memories import router as memories_router

__all__ = [
    "assessments_router",
    "conversations_router",
    "auth_router",
    "users_router",
    "subscriptions_router",
    "star_router",
    "memories_router",
]
