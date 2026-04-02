# -*- coding: utf-8 -*-
"""
深觅 AI Coach - FastAPI主应用入口

本模块是FastAPI应用的主入口，整合所有路由和服务
"""

import os
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import logging

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# 导入路由
from routers import (
    conversations_router,
    assessments_router,
    auth_router,
    users_router,
    subscriptions_router,
    star_router,
    memories_router,
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    # 启动时执行
    logger.info("=" * 50)
    logger.info("深觅 AI Coach 服务启动中...")
    logger.info("=" * 50)
    
    # 初始化服务
    try:
        from services import init_emotion_analyzer, init_chat_service
        from services.litellm_service import init_litellm_service
        
        # 初始化LiteLLM服务（新的统一路由服务）
        init_litellm_service()
        logger.info("LiteLLM服务初始化成功")
        
        # 初始化情感分析器
        init_emotion_analyzer(use_llm=False)
        logger.info("情感分析器初始化成功")
        
        # 初始化对话服务
        init_chat_service()
        logger.info("对话服务初始化成功")
        
    except Exception as e:
        logger.error(f"服务初始化失败: {e}")
        # 继续启动，允许服务在降级模式下运行
    
    logger.info("服务启动完成！")
    
    yield
    
    # 关闭时执行
    logger.info("服务关闭中...")


# 创建FastAPI应用
app = FastAPI(
    title="深觅 AI Coach API",
    description="基于AI的优势教练对话系统",
    version="1.0.0",
    lifespan=lifespan
)

# 配置CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 生产环境应配置具体的域名
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# 全局异常处理
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """全局异常处理"""
    logger.error(f"全局异常: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "code": 500,
            "message": "服务器内部错误",
            "detail": str(exc) if os.getenv("DEBUG") == "true" else "请稍后重试"
        }
    )


# 健康检查
@app.get("/health", tags=["系统"])
async def health_check():
    """健康检查接口"""
    return {
        "status": "healthy",
        "service": "深觅 AI Coach",
        "version": "1.0.0"
    }


# 根路径
@app.get("/", tags=["系统"])
async def root():
    """根路径"""
    return {
        "message": "欢迎使用深觅 AI Coach API",
        "version": "1.0.0",
        "docs": "/docs"
    }


# 注册路由
app.include_router(
    auth_router,
    prefix="/api/v1/auth",
    tags=["认证"]
)

app.include_router(
    users_router,
    prefix="/api/v1/users",
    tags=["用户"]
)

app.include_router(
    conversations_router,
    prefix="/api/v1/conversations",
    tags=["对话系统"]
)

app.include_router(
    assessments_router,
    prefix="/api/v1/assessments",
    tags=["测评"]
)

app.include_router(
    subscriptions_router,
    prefix="/api/v1/subscriptions",
    tags=["订阅"]
)

app.include_router(
    star_router,
    prefix="/api/v1/star",
    tags=["星图"]
)

app.include_router(
    memories_router,
    prefix="/api/v1/memories",
    tags=["记忆系统"]
)


if __name__ == "__main__":
    import uvicorn
    
    # 从环境变量获取配置
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", "8080"))
    reload = os.getenv("DEBUG", "false").lower() == "true"
    
    # 启动服务
    uvicorn.run(
        "main:app",
        host=host,
        port=port,
        reload=reload,
        log_level="info"
    )
