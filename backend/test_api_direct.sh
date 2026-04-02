#!/bin/bash
# LLM API 直连测试脚本

set -e

CONFIG_FILE="/root/.openclaw/workspace/AICOACH/shenmi4/backend/.env"

echo "=========================================="
echo "AI Coach LLM API 连接测试"
echo "=========================================="

# 读取API密钥
KIMI_KEY=$(grep "KIMI_API_KEY=" "$CONFIG_FILE" | cut -d'=' -f2 | tr -d '"')

if [ -z "$KIMI_KEY" ] || [ "$KIMI_KEY" = "your-kimi-api-key-here" ]; then
    echo "❌ 错误: KIMI_API_KEY 未配置"
    echo ""
    echo "请编辑文件: $CONFIG_FILE"
    echo "将 KIMI_API_KEY=your-kimi-api-key-here"
    echo "改为: KIMI_API_KEY=sk-你的真实密钥"
    exit 1
fi

echo "✅ API密钥已配置: ${KIMI_KEY:0:10}..."
echo ""

# 测试API连接
echo "[1] 测试模型列表..."
HTTP_CODE=$(curl -s -o /tmp/kimi_models.json -w "%{http_code}" \
    -H "Authorization: Bearer $KIMI_KEY" \
    https://api.moonshot.cn/v1/models)

if [ "$HTTP_CODE" = "200" ]; then
    echo "✅ API连接成功"
    echo "   可用模型:"
    cat /tmp/kimi_models.json | grep '"id"' | head -5
else
    echo "❌ API连接失败 (HTTP $HTTP_CODE)"
    cat /tmp/kimi_models.json
    exit 1
fi

echo ""
echo "[2] 测试对话..."
curl -s -X POST https://api.moonshot.cn/v1/chat/completions \
    -H "Authorization: Bearer $KIMI_KEY" \
    -H "Content-Type: application/json" \
    -d '{
        "model": "kimi-k2-turbo-preview",
        "messages": [{"role": "user", "content": "你好，回复'测试成功'"}],
        "max_tokens": 50
    }' > /tmp/kimi_chat.json

if grep -q "choices" /tmp/kimi_chat.json; then
    echo "✅ 对话测试成功"
    echo "   回复内容:"
    cat /tmp/kimi_chat.json | grep -o '"content":"[^"]*"' | head -1 | cut -d'"' -f4
else
    echo "❌ 对话测试失败"
    cat /tmp/kimi_chat.json
    exit 1
fi

echo ""
echo "=========================================="
echo "🎉 所有API测试通过！"
echo "=========================================="
echo ""
echo "现在可以重启后端服务:"
echo "  docker compose restart backend"
