#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
LLM连接测试脚本

使用方法:
1. 确保 KIMI_API_KEY 已配置在 .env 文件中
2. 运行: python3 test_llm_connection.py
"""

import asyncio
import sys
import os

# 添加backend到路径
sys.path.insert(0, '/root/.openclaw/workspace/AICOACH/shenmi4/backend')

async def test_connection():
    """测试LLM连接"""
    print("=" * 50)
    print("AI Coach LLM 连接测试")
    print("=" * 50)
    
    # 1. 检查环境变量
    print("\n[1] 检查API密钥...")
    from settings import settings
    
    kimi_key = settings.KIMI_API_KEY
    if not kimi_key or kimi_key == "your-kimi-api-key-here":
        print("❌ KIMI_API_KEY 未配置或为占位符")
        print("   请编辑 backend/.env 文件，填写真实的API密钥")
        return False
    
    print(f"✅ API密钥已配置: {kimi_key[:10]}...")
    
    # 2. 初始化服务
    print("\n[2] 初始化LiteLLM服务...")
    try:
        from services.litellm_service import get_litellm_service
        service = get_litellm_service()
        print("✅ LiteLLM服务初始化成功")
    except Exception as e:
        print(f"❌ 服务初始化失败: {e}")
        return False
    
    # 3. 测试简单对话
    print("\n[3] 测试简单对话...")
    try:
        response = await service.chat(
            messages=[{"role": "user", "content": "你好，请回复'连接测试成功'"}],
            model="kimi-k2-turbo-preview",
            max_tokens=100
        )
        print(f"✅ 对话测试成功")
        print(f"   模型: {response.model}")
        print(f"   回复: {response.content[:100]}...")
        print(f"   Token使用: {response.tokens_used}")
    except Exception as e:
        print(f"❌ 对话测试失败: {e}")
        return False
    
    # 4. 测试结构化输出
    print("\n[4] 测试结构化输出...")
    try:
        from services.litellm_service import CoachIntent
        intent = await service.extract_intent("我想设定一个职业目标")
        print(f"✅ 结构化输出成功")
        print(f"   意图类型: {intent.intent_type}")
        print(f"   置信度: {intent.confidence}")
    except Exception as e:
        print(f"❌ 结构化输出失败: {e}")
        return False
    
    # 5. 测试回退策略
    print("\n[5] 测试模型回退...")
    try:
        # 使用别名测试
        response = await service.chat(
            messages=[{"role": "user", "content": "测试回退策略"}],
            model="coach-chat",  # 使用别名
            max_tokens=50
        )
        print(f"✅ 模型别名/回退测试成功")
        print(f"   实际使用模型: {response.model}")
    except Exception as e:
        print(f"❌ 回退测试失败: {e}")
        return False
    
    print("\n" + "=" * 50)
    print("🎉 所有测试通过！LLM连接正常")
    print("=" * 50)
    return True

if __name__ == "__main__":
    result = asyncio.run(test_connection())
    sys.exit(0 if result else 1)
