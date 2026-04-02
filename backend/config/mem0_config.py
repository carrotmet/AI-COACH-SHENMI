# -*- coding: utf-8 -*-
"""
Mem0 记忆系统配置
完全本地化配置，使用 Chroma 向量存储
"""

import os
from mem0 import Memory

# Mem0 配置（完全本地化）
import os

# 从环境变量读取 API 配置，默认使用 Kimi
LLM_API_KEY = os.getenv("LAZYLLM_KIMI_API_KEY", "")
LLM_API_BASE = os.getenv("LLM_API_BASE", "https://api.moonshot.cn/v1")
LLM_MODEL = os.getenv("MEM0_LLM_MODEL", "openai/kimi-k2-turbo-preview")

MEM0_CONFIG = {
    "vector_store": {
        "provider": "chroma",
        "config": {
            "path": "./data/mem0_chroma",
            "collection_name": "shenmi_memories"
        }
    },
    "llm": {
        "provider": "litellm",
        "config": {
            "model": LLM_MODEL,
            "api_key": LLM_API_KEY,
            "api_base": LLM_API_BASE,
            "temperature": 0.1,   # 提取记忆需要稳定输出
            "max_tokens": 500
        }
    },
    "embedder": {
        "provider": "litellm",
        "config": {
            "model": "openai/text-embedding-3-small",
            "api_key": LLM_API_KEY,
            "api_base": LLM_API_BASE,
            "embedding_dims": 1536
        }
    }
}

# 全局内存实例（单例模式）
_mem0_instance = None

def get_mem0():
    """获取 Mem0 实例（单例）"""
    global _mem0_instance
    if _mem0_instance is None:
        # 确保目录存在
        os.makedirs("./data/mem0_chroma", exist_ok=True)
        _mem0_instance = Memory.from_config(MEM0_CONFIG)
    return _mem0_instance
