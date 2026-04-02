# -*- coding: utf-8 -*-
"""
直接检查OpenAPI中的路由定义详情
"""
import json
import urllib.request

url = 'http://localhost:8081/openapi.json'
with urllib.request.urlopen(url) as resp:
    data = json.loads(resp.read().decode())

# 检查auth路径的具体定义
print("=== /api/v1/auth/auth/register 的定义 ===")
path_item = data.get('paths', {}).get('/api/v1/auth/auth/register', {})
print(json.dumps(path_item, indent=2, ensure_ascii=False))

print("\n=== /api/v1/auth/register 的定义 ===")
path_item2 = data.get('paths', {}).get('/api/v1/auth/register', {})
print(json.dumps(path_item2, indent=2, ensure_ascii=False) if path_item2 else "不存在")

print("\n=== /api/v1/assessments/assessments 的定义 ===")
path_item3 = data.get('paths', {}).get('/api/v1/assessments/assessments', {})
print(json.dumps(path_item3, indent=2, ensure_ascii=False) if path_item3 else "不存在")
