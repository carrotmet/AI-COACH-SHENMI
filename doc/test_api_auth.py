# -*- coding: utf-8 -*-
"""
测试认证API - 使用正确的路径
"""
import aiohttp
import asyncio

async def test_auth():
    """测试认证API"""
    print("=== 测试认证API ===\n")
    
    # 测试路径
    test_paths = [
        '/api/v1/auth/auth/login',  # 运行中的服务使用的路径
        '/api/v1/auth/login',         # 正确的路径
    ]
    
    test_email = 'test@example.com'
    test_password = 'test123456'
    data = {'email': test_email, 'password': test_password}
    
    for path in test_paths:
        url = f'http://localhost:8081{path}'
        print(f"测试路径: {path}")
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(url, json=data, timeout=aiohttp.ClientTimeout(total=10)) as resp:
                    text = await resp.text()
                    print(f"  Status: {resp.status}")
                    print(f"  Response: {text[:200]}")
        except Exception as e:
            print(f"  Error: {e}")
        print()

if __name__ == "__main__":
    asyncio.run(test_auth())
