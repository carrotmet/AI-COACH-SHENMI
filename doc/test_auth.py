# -*- coding: utf-8 -*-
"""
深觅 AI Coach - 注册登录测试脚本

该脚本用于测试用户注册和登录功能，排查认证相关问题。

使用方法:
    python doc/test_auth.py

依赖:
    pip install requests httpx
"""

import asyncio
import json
import sys
import os
from datetime import datetime
from typing import Optional, Dict, Any

# 添加backend目录到Python路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

# 配置常量
API_BASE_URL = "http://localhost/api/v1"
TEST_EMAIL = f"test_{int(datetime.now().timestamp())}@example.com"
TEST_PASSWORD = "test123456"
TEST_NICKNAME = "测试用户"


def print_section(title: str) -> None:
    """打印分节标题"""
    print(f"\n{'='*60}")
    print(f"  {title}")
    print('='*60)


def print_result(name: str, success: bool, detail: str = "") -> None:
    """打印测试结果"""
    status = "✓ 通过" if success else "✗ 失败"
    print(f"  [{status}] {name}")
    if detail:
        print(f"       {detail}")


async def test_health_check() -> bool:
    """测试健康检查接口"""
    print_section("1. 健康检查测试")
    
    try:
        import aiohttp
        async with aiohttp.ClientSession() as session:
            async with session.get(f"{API_BASE_URL.replace('/api/v1', '')}/health") as resp:
                if resp.status == 200:
                    data = await resp.json()
                    print_result("服务运行中", True, f"响应: {data}")
                    return True
                else:
                    print_result("服务运行中", False, f"HTTP状态码: {resp.status}")
                    return False
    except Exception as e:
        print_result("服务运行中", False, f"错误: {str(e)}")
        return False


async def test_register() -> Optional[Dict[str, Any]]:
    """测试用户注册"""
    print_section("2. 用户注册测试")
    
    import aiohttp
    
    payload = {
        "email": TEST_EMAIL,
        "password": TEST_PASSWORD,
        "nickname": TEST_NICKNAME
    }
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{API_BASE_URL}/auth/register",
                json=payload,
                timeout=aiohttp.ClientTimeout(total=30)
            ) as resp:
                status = resp.status
                text = await resp.text()
                
                try:
                    data = json.loads(text)
                except:
                    data = {"raw_response": text}
                
                if status == 201 or status == 200:
                    if data.get("code") in [200, 201]:
                        print_result("用户注册", True, f"邮箱: {TEST_EMAIL}")
                        print(f"       响应数据: {json.dumps(data, ensure_ascii=False, indent=8)}")
                        return data.get("data")
                    else:
                        print_result("用户注册", False, f"业务错误: {data.get('message')}")
                        print(f"       错误详情: {json.dumps(data, ensure_ascii=False, indent=8)}")
                        return None
                else:
                    print_result("用户注册", False, f"HTTP状态: {status}")
                    print(f"       响应: {json.dumps(data, ensure_ascii=False, indent=8)}")
                    return None
    except Exception as e:
        print_result("用户注册", False, f"异常: {str(e)}")
        import traceback
        traceback.print_exc()
        return None


async def test_login(email: str, password: str) -> Optional[Dict[str, Any]]:
    """测试用户登录"""
    print_section("3. 用户登录测试")
    
    import aiohttp
    
    payload = {
        "email": email,
        "password": password
    }
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{API_BASE_URL}/auth/login",
                json=payload,
                timeout=aiohttp.ClientTimeout(total=30)
            ) as resp:
                status = resp.status
                text = await resp.text()
                
                try:
                    data = json.loads(text)
                except:
                    data = {"raw_response": text}
                
                if status == 200:
                    if data.get("code") == 200:
                        print_result("用户登录", True, f"邮箱: {email}")
                        print(f"       响应数据: {json.dumps(data, ensure_ascii=False, indent=8)}")
                        return data.get("data")
                    else:
                        print_result("用户登录", False, f"业务错误: {data.get('message')}")
                        print(f"       错误详情: {json.dumps(data, ensure_ascii=False, indent=8)}")
                        return None
                else:
                    print_result("用户登录", False, f"HTTP状态: {status}")
                    print(f"       响应: {json.dumps(data, ensure_ascii=False, indent=8)}")
                    return None
    except Exception as e:
        print_result("用户登录", False, f"异常: {str(e)}")
        import traceback
        traceback.print_exc()
        return None


async def test_get_current_user(access_token: str) -> Optional[Dict[str, Any]]:
    """测试获取当前用户信息"""
    print_section("4. 获取当前用户信息测试")
    
    import aiohttp
    
    try:
        async with aiohttp.ClientSession() as session:
            headers = {"Authorization": f"Bearer {access_token}"}
            async with session.get(
                f"{API_BASE_URL}/auth/me",
                headers=headers,
                timeout=aiohttp.ClientTimeout(total=30)
            ) as resp:
                status = resp.status
                text = await resp.text()
                
                try:
                    data = json.loads(text)
                except:
                    data = {"raw_response": text}
                
                if status == 200:
                    if data.get("code") == 200:
                        print_result("获取用户信息", True)
                        print(f"       用户数据: {json.dumps(data.get('data'), ensure_ascii=False, indent=8)}")
                        return data.get("data")
                    else:
                        print_result("获取用户信息", False, f"业务错误: {data.get('message')}")
                        return None
                else:
                    print_result("获取用户信息", False, f"HTTP状态: {status}")
                    print(f"       响应: {json.dumps(data, ensure_ascii=False, indent=8)}")
                    return None
    except Exception as e:
        print_result("获取用户信息", False, f"异常: {str(e)}")
        import traceback
        traceback.print_exc()
        return None


async def test_login_with_wrong_password(email: str) -> None:
    """测试错误密码登录"""
    print_section("5. 错误密码登录测试")
    
    import aiohttp
    
    payload = {
        "email": email,
        "password": "wrong_password_12345"
    }
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{API_BASE_URL}/auth/login",
                json=payload,
                timeout=aiohttp.ClientTimeout(total=30)
            ) as resp:
                status = resp.status
                text = await resp.text()
                
                try:
                    data = json.loads(text)
                except:
                    data = {"raw_response": text}
                
                if status == 401 and data.get("code") == 1200:
                    print_result("错误密码拒绝", True, "正确拒绝错误密码")
                else:
                    print_result("错误密码拒绝", False, f"预期401错误，实际: {status}")
                    print(f"       响应: {json.dumps(data, ensure_ascii=False, indent=8)}")
    except Exception as e:
        print_result("错误密码拒绝", False, f"异常: {str(e)}")


async def test_login_nonexistent_user() -> None:
    """测试不存在的用户登录"""
    print_section("6. 不存在用户登录测试")
    
    import aiohttp
    
    payload = {
        "email": "nonexistent_user_12345@example.com",
        "password": "any_password"
    }
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{API_BASE_URL}/auth/login",
                json=payload,
                timeout=aiohttp.ClientTimeout(total=30)
            ) as resp:
                status = resp.status
                text = await resp.text()
                
                try:
                    data = json.loads(text)
                except:
                    data = {"raw_response": text}
                
                if status == 401 and data.get("code") == 1100:
                    print_result("不存在的用户", True, "正确拒绝不存在的用户")
                else:
                    print_result("不存在的用户", False, f"预期401错误，实际: {status}")
                    print(f"       响应: {json.dumps(data, ensure_ascii=False, indent=8)}")
    except Exception as e:
        print_result("不存在的用户", False, f"异常: {str(e)}")


async def check_database_users() -> None:
    """检查数据库中的用户"""
    print_section("7. 数据库用户检查")
    
    try:
        import aiosqlite
        
        db_path = os.path.join(os.path.dirname(__file__), '..', 'backend', 'data', 'ai_coach.db')
        if not os.path.exists(db_path):
            db_path = os.path.join(os.path.dirname(__file__), '..', 'backend', 'ai_coach.db')
        
        if not os.path.exists(db_path):
            print_result("数据库检查", False, f"数据库文件不存在: {db_path}")
            return
        
        async with aiosqlite.connect(db_path) as db:
            # 检查用户表
            cursor = await db.execute("SELECT id, username, email, status, subscription_type, created_at FROM users LIMIT 10")
            users = await cursor.fetchall()
            
            if users:
                print(f"  数据库中的用户 (共{len(users)}条):")
                for user in users:
                    print(f"    ID: {user[0]}, 用户名: {user[1]}, 邮箱: {user[2]}, 状态: {user[3]}, 订阅: {user[4]}, 创建时间: {user[5]}")
                print_result("数据库检查", True)
            else:
                print_result("数据库检查", True, "数据库中暂无用户")
                
            # 检查user_tokens表
            cursor = await db.execute("SELECT id, user_id, token_type, revoked, expires_at FROM user_tokens LIMIT 5")
            tokens = await cursor.fetchall()
            
            if tokens:
                print(f"  数据库中的Token (共{len(tokens)}条):")
                for token in tokens:
                    print(f"    ID: {token[0]}, 用户ID: {token[1]}, 类型: {token[2]}, 撤销: {token[3]}, 过期: {token[4]}")
            else:
                print("  数据库中暂无Token记录")
                
    except Exception as e:
        print_result("数据库检查", False, f"异常: {str(e)}")
        import traceback
        traceback.print_exc()


async def main():
    """主函数"""
    print("\n" + "="*60)
    print("  深觅 AI Coach - 注册登录测试")
    print("="*60)
    print(f"  测试时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"  API地址: {API_BASE_URL}")
    print(f"  测试邮箱: {TEST_EMAIL}")
    
    # 1. 检查服务是否运行
    service_ok = await test_health_check()
    if not service_ok:
        print("\n[错误] 后端服务未运行或无法访问")
        print("请先启动后端服务: cd backend && python main.py")
        return
    
    # 2. 测试注册
    register_data = await test_register()
    
    # 3. 如果注册成功，测试登录
    if register_data:
        login_data = await test_login(TEST_EMAIL, TEST_PASSWORD)
        
        # 4. 测试获取当前用户信息
        if login_data and login_data.get("access_token"):
            await test_get_current_user(login_data["access_token"])
        
        # 5. 测试错误密码
        await test_login_with_wrong_password(TEST_EMAIL)
    else:
        # 尝试使用已存在的邮箱登录（如果有）
        print("\n注册失败，尝试登录已存在的用户...")
        await test_login("admin@example.com", "admin123")
    
    # 6. 测试不存在的用户
    await test_login_nonexistent_user()
    
    # 7. 检查数据库
    await check_database_users()
    
    # 总结
    print("\n" + "="*60)
    print("  测试完成")
    print("="*60)


if __name__ == "__main__":
    asyncio.run(main())
