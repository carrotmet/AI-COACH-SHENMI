# -*- coding: utf-8 -*-
"""
深觅 AI Coach - 中间件模块

该模块提供各种FastAPI中间件
"""

from middleware.auth_middleware import AuthMiddleware, get_current_user

__all__ = [
    "AuthMiddleware",
    "get_current_user",
]
