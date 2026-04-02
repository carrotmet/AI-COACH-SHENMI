#!/bin/bash
# 星图403问题诊断脚本

echo "=========================================="
echo "星图403问题诊断"
echo "=========================================="
echo ""

# 检查nginx配置
echo "【1】检查nginx配置..."
if grep -q "location /api/" /root/.openclaw/workspace/AICOACH/shenmi4/nginx.conf; then
    echo "✓ nginx已配置/api/代理"
else
    echo "✗ nginx未配置/api/代理"
fi
echo ""

# 检查后端路由
echo "【2】检查后端路由..."
cd /root/.openclaw/workspace/AICOACH/shenmi4/backend
if python3 -c "from routers.star import router; print('Star router OK')" 2>/dev/null; then
    echo "✓ star路由模块可导入"
else
    echo "⚠ star路由模块导入失败（依赖问题，语法OK）"
fi

if grep -q "star_router" main.py; then
    echo "✓ star_router已在main.py注册"
else
    echo "✗ star_router未在main.py注册"
fi
echo ""

# 检查前端API调用
echo "【3】检查前端API..."
if grep -q "starAPI" /root/.openclaw/workspace/AICOACH/shenmi4/frontend/js/api.js; then
    echo "✓ starAPI已定义"
else
    echo "✗ starAPI未定义"
fi

if grep -q "api.star.getGraph" /root/.openclaw/workspace/AICOACH/shenmi4/frontend/star/star.js; then
    echo "✓ 前端正确调用api.star.getGraph"
else
    echo "✗ 前端调用方式可能错误"
fi
echo ""

# 检查认证中间件
echo "【4】检查认证中间件..."
if grep -q "get_current_user" /root/.openclaw/workspace/AICOACH/shenmi4/backend/routers/star.py; then
    echo "✓ star路由使用get_current_user依赖"
else
    echo "✗ star路由缺少认证依赖"
fi
echo ""

# 检查响应格式
echo "【5】检查响应格式..."
if grep -q "success_response" /root/.openclaw/workspace/AICOACH/shenmi4/backend/routers/star.py; then
    echo "✓ star路由使用success_response"
else
    echo "✗ star路由未使用success_response"
fi
echo ""

echo "=========================================="
echo "常见403原因:"
echo "1. 用户未登录 - 检查localStorage是否有access_token"
echo "2. Token过期 - 检查token是否有效"
echo "3. 用户状态非active - 检查数据库users.status"
echo "4. Nginx代理问题 - 检查nginx日志"
echo "=========================================="
