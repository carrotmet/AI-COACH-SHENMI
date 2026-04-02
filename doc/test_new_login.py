# -*- coding: utf-8 -*-
"""测试新注册用户的登录"""
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))
os.chdir(os.path.join(os.path.dirname(__file__), '..', 'backend'))

import asyncio
from database.connection import async_session
from services.auth_service import AuthService

async def test_new_user_login():
    """测试新注册用户登录"""
    print("=== 测试新注册用户登录 ===\n")
    
    # 先注册一个新用户
    test_email = f"newuser_test@example.com"
    test_password = "test123456"
    
    async with async_session() as db:
        auth_service = AuthService(db)
        
        # 注册
        print(f"1. 注册新用户: {test_email}")
        result, error_code, error_detail = await auth_service.register(
            email=test_email,
            password=test_password,
            nickname="测试用户"
        )
        
        if error_code:
            print(f"   注册失败: {error_code} - {error_detail}")
        else:
            print(f"   注册成功! user_id={result.get('user_id')}")
        
        # 登录
        print(f"\n2. 测试登录: {test_email}")
        result2, error_code2, error_detail2 = await auth_service.login(
            email=test_email,
            password=test_password
        )
        
        if error_code2:
            print(f"   登录失败: {error_code2} - {error_detail2}")
        else:
            print(f"   登录成功! user_id={result2.get('user_id')}")
            print(f"   access_token: {result2.get('access_token')[:50]}...")

if __name__ == "__main__":
    asyncio.run(test_new_user_login())
