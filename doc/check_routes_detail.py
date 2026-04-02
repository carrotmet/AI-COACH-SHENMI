# -*- coding: utf-8 -*-
"""
详细检查运行中app的路由注册
"""
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

# 导入app但不启动
os.environ.setdefault('PYTHONPATH', os.path.dirname(__file__) + '/../backend')

from main import app

print("=== 已注册的路由 ===")
for route in app.routes:
    if hasattr(route, 'path'):
        # 获取router的prefix属性
        prefix = getattr(route, 'prefix', '')
        # 获取对应的endpoints
        if hasattr(route, 'routes'):
            for r in route.routes:
                if hasattr(r, 'path'):
                    print(f"  {prefix}{r.path} -> {getattr(r, 'methods', 'N/A')}")
        else:
            print(f"  {route.path}")
