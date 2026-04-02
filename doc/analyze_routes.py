# -*- coding: utf-8 -*-
"""
详细分析路由问题
"""
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))
os.chdir(os.path.join(os.path.dirname(__file__), '..', 'backend'))

# 直接打印main.py中的路由注册
print("=== main.py中的路由注册 ===")
with open('main.py', 'r', encoding='utf-8') as f:
    content = f.read()
    # 查找所有include_router调用
    import re
    matches = re.findall(r'app\.include_router\((.*?)\)', content, re.DOTALL)
    for m in matches:
        print(m[:200])

print("\n=== routers/__init__.py ===")
with open('routers/__init__.py', 'r', encoding='utf-8') as f:
    print(f.read())

print("\n=== 检查是否有重复导入 ===")
# 检查main.py中是否多次导入同一个router
import re
import_main = re.findall(r'from routers\.(\w+) import', content)
print(f"从routers导入: {import_main}")
