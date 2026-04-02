# -*- coding: utf-8 -*-
"""
检查所有router文件的定义
"""
import sys
import os
import re

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

# 检查每个router文件
router_files = [
    'routers/auth.py',
    'routers/users.py', 
    'routers/conversations.py',
    'routers/assessments.py',
    'routers/subscriptions.py'
]

for rf in router_files:
    filepath = os.path.join(os.path.dirname(__file__), '..', 'backend', rf)
    if os.path.exists(filepath):
        print(f"\n=== {rf} ===")
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
            # 查找APIRouter定义
            matches = re.findall(r'router\s*=\s*APIRouter\((.*?)\)', content, re.DOTALL)
            for m in matches:
                print(f"  APIRouter定义: {m[:200]}...")
