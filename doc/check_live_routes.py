# -*- coding: utf-8 -*-
"""
检查运行中服务的路由
"""
import sys
import json
import urllib.request

# 获取运行中服务的OpenAPI定义
url = 'http://localhost:8081/openapi.json'
try:
    with urllib.request.urlopen(url) as resp:
        data = json.loads(resp.read().decode())
        
    print("=== Auth相关路由 ===")
    for path in sorted(data.get('paths', {}).keys()):
        if 'auth' in path.lower():
            print(f"  {path}")
            
    print("\n=== 所有路由 ===")
    for path in sorted(data.get('paths', {}).keys()):
        print(f"  {path}")
        
except Exception as e:
    print(f"Error: {e}")
