# -*- coding: utf-8 -*-
"""
直接测试认证服务，查看具体错误
"""
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))
os.chdir(os.path.join(os.path.dirname(__file__), '..', 'backend'))

import asyncio
from database.connection import async_session
from services.auth_service import AuthService

async def test_register():
    """测试注册"""
    print("=== 测试用户注册 ===")
    async with async_session() as db:
        auth_service = AuthService(db)
        try:
            result, error_code, error_detail = await auth_service.register(
                email="debug_test@example.com",
                password="test123456",
                nickname="调试用户"
            )
            if error_code:
                print(f"注册失败: {error_code} - {error_detail}")
            else:
                print(f"注册成功! user_id={result.get('user_id')}")
                print(f"access_token: {result.get('access_token')[:50]}...")
        except Exception as e:
            print(f"注册异常: {type(e).__name__}: {e}")
            import traceback
            traceback.print_exc()

async def test_login():
    """测试登录"""
    print("\n=== 测试用户登录 ===")
    async with async_session() as db:
        auth_service = AuthService(db)
        try:
            result, error_code, error_detail = await auth_service.login(
                email="test@test.com",
                password="test123"
            )
            if error_code:
                print(f"登录失败: {error_code} - {error_detail}")
            else:
                print(f"登录成功! user_id={result.get('user_id')}")
                print(f"access_token: {result.get('access_token')[:50]}...")
        except Exception as e:
            print(f"登录异常: {type(e).__name__}: {e}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    print("直接测试认证服务...\n")
    asyncio.run(test_register())
    asyncio.run(test_login())
