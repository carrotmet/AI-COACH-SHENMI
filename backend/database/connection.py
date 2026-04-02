# -*- coding: utf-8 -*-
"""
深觅 AI Coach - 数据库连接模块

该模块负责：
- SQLAlchemy异步引擎创建
- 异步会话管理
- 数据库初始化和关闭
"""

from typing import AsyncGenerator
from contextlib import asynccontextmanager

from sqlalchemy.ext.asyncio import (
    create_async_engine,
    AsyncSession,
    async_sessionmaker,
)
from sqlalchemy import text

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from settings import settings
from database.models import Base


# =====================================================
# 创建异步引擎
# =====================================================
engine = create_async_engine(
    settings.DATABASE_URL,
    echo=settings.DATABASE_ECHO,
    future=True,
)

# =====================================================
# 创建异步会话工厂
# =====================================================
async_session = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)


# =====================================================
# 数据库操作函数
# =====================================================

async def init_db() -> None:
    """
    初始化数据库
    
    创建所有定义的数据表
    
    Raises:
        Exception: 数据库初始化失败时抛出
    """
    try:
        async with engine.begin() as conn:
            # 创建所有表
            await conn.run_sync(Base.metadata.create_all)
        print(f"[OK] 数据库初始化成功: {settings.DATABASE_URL}")
    except Exception as e:
        print(f"[ERROR] 数据库初始化失败: {e}")
        raise


async def close_db() -> None:
    """
    关闭数据库连接
    
    释放所有数据库连接资源
    """
    try:
        await engine.dispose()
        print("[OK] 数据库连接已关闭")
    except Exception as e:
        print(f"[ERROR] 关闭数据库连接失败: {e}")


async def check_db_connection() -> bool:
    """
    检查数据库连接是否正常
    
    Returns:
        bool: 连接正常返回True，否则返回False
    """
    try:
        async with engine.connect() as conn:
            result = await conn.execute(text("SELECT 1"))
            await result.fetchone()
        return True
    except Exception as e:
        print(f"[ERROR] 数据库连接检查失败: {e}")
        return False


@asynccontextmanager
async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    获取数据库会话的异步上下文管理器
    
    使用示例:
        async with get_db() as db:
            result = await db.execute(query)
    
    Yields:
        AsyncSession: 数据库会话对象
    """
    async with async_session() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """
    获取数据库会话（用于FastAPI依赖注入）
    
    使用示例:
        @app.get("/items")
        async def get_items(db: AsyncSession = Depends(get_db_session)):
            ...
    
    Yields:
        AsyncSession: 数据库会话对象
    """
    async with async_session() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()
