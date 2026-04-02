# 深觅 AI Coach - AI对话模块

## 模块概述

本模块实现了深觅 AI Coach 系统的AI对话功能，包括：

- **提示词模板管理** (`prompt_templates.py`) - 优势教练AI角色的提示词模板
- **LLM集成服务** (`llm_service.py`) - 大语言模型集成，支持多种后端
- **情感分析服务** (`emotion_analyzer.py`) - 用户消息情感分析
- **对话服务核心** (`chat_service.py`) - 对话管理和消息处理
- **对话路由** (`conversations.py`) - FastAPI路由接口

## 理论基础

### VIA性格优势模型
系统基于VIA（Values in Action）性格优势理论，包含6大美德领域和24种性格优势：
- 智慧与知识：创造力、好奇心、判断力、热爱学习、洞察力
- 勇气：勇敢、坚韧、正直、活力
- 人道主义：爱与被爱的能力、善良、社交智慧
- 正义：团队合作、公平、领导力
- 节制：宽恕、谦逊、谨慎、自我调节
- 超越：审美、感恩、希望、幽默、灵性

### GROW教练模型
对话中自然运用GROW模型：
- **G (Goal)**：帮助用户明确目标
- **R (Reality)**：探索当前现实状况
- **O (Options)**：探讨可行的选择方案
- **W (Will)**：激发行动意愿，制定具体计划

### DAIC框架
遵循DAIC框架建立教练关系：
- **Discover（发现）**：发现用户的优势和潜能
- **Analyze（分析）**：分析优势应用场景和发展机会
- **Implement（实施）**：协助制定和实施行动计划
- **Consolidate（巩固）**：巩固成果，持续成长

## 目录结构

```
backend/
├── main.py                    # FastAPI主应用入口
├── README.md                  # 本文件
├── services/                  # 服务模块
│   ├── __init__.py
│   ├── prompt_templates.py   # 提示词模板
│   ├── llm_service.py        # LLM集成服务
│   ├── emotion_analyzer.py   # 情感分析服务
│   └── chat_service.py       # 对话服务核心
└── routers/                   # 路由模块
    ├── __init__.py
    └── conversations.py       # 对话路由
```

## 安装依赖

```bash
pip install fastapi uvicorn pydantic
pip install openai  # 如果使用OpenAI API
pip install anthropic  # 如果使用Claude API
# pip install lazyllm  # 如果使用LazyLLM框架
```

## 环境变量配置

```bash
# LLM配置
export OPENAI_API_KEY="your-api-key"
export OPENAI_BASE_URL="https://api.openai.com/v1"  # 可选
export LLM_MODEL="gpt-4o-mini"

# 服务配置
export HOST="0.0.0.0"
export PORT="8000"
export DEBUG="true"
```

## 快速开始

### 1. 启动服务

```bash
cd backend
python main.py
```

或使用uvicorn直接启动：

```bash
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

### 2. 访问API文档

启动后访问：http://localhost:8000/docs

### 3. 测试对话API

```bash
# 创建对话
curl -X POST "http://localhost:8000/api/v1/conversations" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "优势探索对话",
    "coach_type": "strength"
  }'

# 发送消息
curl -X POST "http://localhost:8000/api/v1/conversations/{conversation_id}/messages" \
  -H "Content-Type: application/json" \
  -d '{
    "content": "你好，我想了解我的优势"
  }'

# 获取消息历史
curl "http://localhost:8000/api/v1/conversations/{conversation_id}/messages"

# 获取对话列表
curl "http://localhost:8000/api/v1/conversations"

# 删除对话
curl -X DELETE "http://localhost:8000/api/v1/conversations/{conversation_id}"
```

## API接口列表

| 接口 | 方法 | 路径 | 说明 |
|-----|------|------|------|
| 创建对话 | POST | /api/v1/conversations | 创建新对话 |
| 获取对话列表 | GET | /api/v1/conversations | 获取用户对话列表 |
| 获取对话详情 | GET | /api/v1/conversations/{id} | 获取对话详情 |
| 发送消息 | POST | /api/v1/conversations/{id}/messages | 发送消息 |
| 获取消息历史 | GET | /api/v1/conversations/{id}/messages | 获取消息历史 |
| 删除对话 | DELETE | /api/v1/conversations/{id} | 删除对话 |
| 获取对话摘要 | GET | /api/v1/conversations/{id}/summary | 获取AI生成摘要 |
| 获取对话限制 | GET | /api/v1/conversations/limits | 获取配额信息 |

## 核心功能使用

### 使用提示词模板

```python
from services import get_system_prompt, PromptManager, PromptType

# 获取系统提示词
system_prompt = get_system_prompt(
    user_profile={"nickname": "小明", "occupation": "工程师"},
    strength_profile={
        "top_strengths": [
            {"name": "战略思维", "score": 92},
            {"name": "学习力", "score": 88}
        ]
    }
)

# 使用提示词管理器
manager = PromptManager()
greeting = manager.render_template(
    PromptType.GREETING,
    is_first_conversation=True
)
```

### 使用LLM服务

```python
from services import LLMService, LLMConfig, LLMProvider

# 创建配置
config = LLMConfig(
    provider=LLMProvider.OPENAI,
    model="gpt-4o-mini",
    api_key="your-api-key",
    temperature=0.7,
    max_tokens=2000
)

# 初始化服务
llm = LLMService(config)

# 发送对话请求
response = await llm.chat(
    messages=[
        {"role": "user", "content": "你好"}
    ],
    system_prompt="你是一位优势教练"
)

print(response.content)
print(f"Token使用: {response.tokens_used}")
```

### 使用情感分析

```python
from services import analyze_emotion, get_emotion_analyzer

# 快速分析
result = await analyze_emotion("今天真的很开心！")
print(f"情感: {result.emotion_label}")
print(f"强度: {result.intensity}")

# 使用分析器实例
analyzer = get_emotion_analyzer(use_llm=False)
result = await analyzer.analyze("感到很焦虑")
print(f"建议: {result.suggestions}")
```

### 使用对话服务

```python
from services import get_chat_service

# 获取服务实例
chat_service = get_chat_service()

# 创建对话
conversation = await chat_service.create_conversation(
    user_id="user_123",
    title="优势探索"
)

# 发送消息
response = await chat_service.send_message(
    conversation_id=conversation.id,
    content="我想了解我的优势"
)

print(f"AI回复: {response.ai_message.content}")

# 获取历史
messages = await chat_service.get_conversation_history(
    conversation_id=conversation.id
)
```

## 对话流程

```
用户发送消息
    ↓
情感分析（识别情绪标签和强度）
    ↓
构建Prompt（系统提示词 + 用户画像 + 优势档案 + 对话历史）
    ↓
LLM生成回复
    ↓
保存消息（用户消息 + AI回复）
    ↓
返回回复（包含情感分析结果）
```

## 提示词模板类型

### 系统提示词
- AI角色设定（深寻 - 优势教练）
- VIA理论基础
- GROW模型指导
- DAIC框架原则
- 对话风格和原则

### 对话策略提示词
- **开场白** - 对话开始时的问候
- **目标探索** - 引导用户明确目标
- **优势分析** - 分析用户优势
- **行动计划** - 协助制定行动计划
- **反思引导** - 引导深度反思
- **结束语** - 对话总结

### 情感回应提示词
- 积极情绪回应
- 消极情绪回应
- 焦虑情绪回应
- 困惑情绪回应
- 沮丧情绪回应
- 兴奋情绪回应
- 感恩情绪回应
- 悲伤情绪回应

## 支持的LLM提供商

- **OpenAI** - GPT-4, GPT-4o, GPT-4o-mini
- **Anthropic** - Claude 3 (Sonnet, Haiku, Opus)
- **Azure OpenAI** - Azure托管的OpenAI模型
- **LazyLLM** - 指定的技术框架
- **Custom** - 自定义OpenAI兼容接口

## 开发计划

### 已完成
- [x] 提示词模板系统
- [x] LLM集成服务（支持多种后端）
- [x] 情感分析服务（规则和LLM两种模式）
- [x] 对话服务核心
- [x] FastAPI路由接口
- [x] 对话配额管理

### 待开发
- [ ] 数据库存储（替换内存存储）
- [ ] 用户认证集成
- [ ] 流式响应支持
- [ ] 对话摘要生成优化
- [ ] 长期记忆机制
- [ ] 多轮对话上下文优化
- [ ] 性能监控和日志

## 贡献指南

1. Fork本仓库
2. 创建功能分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送分支 (`git push origin feature/AmazingFeature`)
5. 创建Pull Request

## 许可证

MIT License

## 联系方式

- 项目主页：https://github.com/shenxunmi/ai-coach
- 问题反馈：https://github.com/shenxunmi/ai-coach/issues
- 邮箱：support@shenxunmi.com
