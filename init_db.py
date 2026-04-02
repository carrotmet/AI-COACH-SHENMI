# -*- coding: utf-8 -*-
"""
深觅 AI Coach - 数据库初始化脚本
"""

import asyncio
import sys
import os

# 添加backend到路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

from database.connection import init_db


async def main():
    """初始化数据库"""
    print("=" * 50)
    print("深觅 AI Coach - 数据库初始化")
    print("=" * 50)
    
    try:
        await init_db()
        print("\n数据库初始化完成！")
        return 0
    except Exception as e:
        print(f"\n数据库初始化失败: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
