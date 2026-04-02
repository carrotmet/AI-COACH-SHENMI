# 深觅 AI Coach - Agent Guide

> This document provides essential information for AI coding agents working on the 深觅 AI Coach project.
> 
> 文档版本: v1.0.0  
> 语言: 中文（项目主要使用中文注释和文档）

---

## 项目概述

**深觅 AI Coach** 是一个基于优势教练理论的AI对话系统，帮助用户发现和发展个人优势，实现自我成长。

### 核心理念

- **优势导向**：基于VIA品格优势理论，聚焦优势发展而非短板弥补
- **AI赋能**：利用大语言模型（OpenAI/Claude）提供个性化教练对话
- **科学方法**：整合积极心理学、GROW模型、DAIC框架
- **用户转化漏斗**：免费测评 → 引流报表 → AI对话体验 → 付费订阅

### 核心功能模块

| 模块 | 功能描述 |
|------|----------|
| 用户认证 | 注册、登录、JWT Token认证 |
| 心理测评 | VIA品格优势评估（24题简化版） |
| AI对话 | 基于大语言模型的优势教练对话 |
| 订阅管理 | 免费/付费订阅等级管理 |
| 用户中心 | 个人资料、历史记录、设置 |

---

## 技术架构

```
┌─────────────────────────────────────────────────────────────┐
│                        用户层                                │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐   │
│  │  Web端   │  │  移动端  │  │  小程序  │  │  管理端  │   │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘   │
└─────────────────────────────────────────────────────────────┘
                              │
┌─────────────────────────────────────────────────────────────┐
│                       网关层 (Nginx)                         │
│              静态文件服务 / API代理 / 负载均衡               │
└─────────────────────────────────────────────────────────────┘
                              │
┌─────────────────────────────────────────────────────────────┐
│                      API层 (FastAPI)                         │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐   │
│  │ 认证模块 │  │ 测评模块 │  │ 对话模块 │  │ 订阅模块 │   │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘   │
└─────────────────────────────────────────────────────────────┘
                              │
┌─────────────────────────────────────────────────────────────┐
│                     服务层 (Services)                        │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐   │
│  │ LLM服务  │  │ 评分引擎 │  │ 报表服务 │  │ 情感分析 │   │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘   │
└─────────────────────────────────────────────────────────────┘
                              │
┌─────────────────────────────────────────────────────────────┐
│                     数据层 (SQLite)                          │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐   │
│  │ 用户数据 │  │ 测评数据 │  │ 对话数据 │  │ 订阅数据 │   │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘   │
└─────────────────────────────────────────────────────────────┘
```

---

## 技术栈

### 后端 (Backend)

| 组件 | 技术 | 版本 | 说明 |
|------|------|------|------|
| 框架 | FastAPI | 0.109.0 | Python Web框架 |
| 服务器 | Uvicorn | 0.27.0 | ASGI服务器 |
| 语言 | Python | 3.10+ | 编程语言 |
| 数据库 | SQLite | 3.0+ | 关系型数据库 |
| ORM | SQLAlchemy | 2.0+ | 数据库ORM |
| 数据验证 | Pydantic | 2.5.3 | 数据模型验证 |
| 认证 | python-jose | - | JWT Token处理 |
| AI集成 | OpenAI SDK | 1.10.0 | OpenAI API |
| AI集成 | Anthropic SDK | 0.18.0 | Claude API |
| HTTP客户端 | httpx/aiohttp | - | 异步HTTP请求 |
| 日志 | structlog | 24.1.0 | 结构化日志 |

### 前端 (Frontend)

| 组件 | 技术 | 说明 |
|------|------|------|
| 技术栈 | 原生 JavaScript (ES6+) | 无框架依赖 |
| 样式 | CSS3 | 响应式设计 |
| UI组件 | 自定义组件库 | 项目内置 |
| 开发服务器 | http-server | 本地开发 |

### 基础设施

| 组件 | 技术 | 说明 |
|------|------|------|
| 容器化 | Docker + Docker Compose | 部署方案 |
| 反向代理 | Nginx | 静态文件服务、API代理 |
| 缓存 | Redis | 可选缓存服务 |

---

## 项目目录结构

```
.
├── backend/                    # 后端代码
│   ├── main.py                 # FastAPI应用入口
│   ├── config.py               # 配置管理（Pydantic Settings）
│   ├── requirements.txt        # Python依赖列表
│   ├── .env                    # 环境变量（需创建）
│   ├── .env.example            # 环境变量示例
│   ├── database/               # 数据库模块
│   │   ├── models.py           # SQLAlchemy ORM模型
│   │   ├── connection.py       # 数据库连接管理
│   │   ├── schema.sql          # 数据库建表脚本
│   │   └── __init__.py
│   ├── routers/                # API路由模块
│   │   ├── auth.py             # 认证路由
│   │   ├── users.py            # 用户管理路由
│   │   ├── assessments.py      # 测评系统路由
│   │   ├── conversations.py    # 对话系统路由
│   │   ├── subscriptions.py    # 订阅管理路由
│   │   └── __init__.py
│   ├── services/               # 业务服务层
│   │   ├── auth_service.py     # 认证服务
│   │   ├── chat_service.py     # 对话服务
│   │   ├── llm_service.py      # LLM服务
│   │   ├── assessment_service.py # 测评服务
│   │   ├── scoring_engine.py   # 评分引擎
│   │   ├── report_service.py   # 报表服务
│   │   ├── emotion_analyzer.py # 情感分析
│   │   └── __init__.py
│   ├── middleware/             # 中间件
│   │   ├── auth_middleware.py  # 认证中间件
│   │   └── __init__.py
│   ├── utils/                  # 工具模块
│   │   ├── security.py         # 安全工具（密码、JWT）
│   │   ├── response.py         # 响应格式封装
│   │   └── __init__.py
│   ├── data/                   # 数据文件
│   │   ├── via_questions.py    # VIA测评题目
│   │   ├── strength_data.py    # 优势定义数据
│   │   └── report_templates.py # 报告模板
│   └── tests/                  # 后端单元测试
│       └── test_chat.py
│
├── frontend/                   # 前端代码
│   ├── index.html              # 首页
│   ├── login.html              # 登录页
│   ├── register.html           # 注册页
│   ├── package.json            # npm配置
│   ├── assessment/             # 测评相关页面
│   │   ├── index.html
│   │   ├── test.html
│   │   └── result.html
│   ├── chat/                   # 对话页面
│   │   └── index.html
│   ├── user/                   # 用户中心
│   │   └── index.html
│   ├── js/                     # JavaScript模块
│   │   ├── api.js              # API调用封装
│   │   ├── auth.js             # 认证相关
│   │   ├── chat.js             # 对话功能
│   │   ├── assessment.js       # 测评功能
│   │   ├── config.js           # 前端配置
│   │   ├── utils.js            # 工具函数
│   │   └── main.js             # 主入口
│   └── styles/                 # CSS样式
│       ├── variables.css       # CSS变量
│       ├── base.css            # 基础样式
│       ├── layout.css          # 布局样式
│       ├── components.css      # 组件样式
│       └── main.css            # 主样式入口
│
├── tests/                      # 集成测试
│   ├── conftest.py             # pytest配置和fixture
│   ├── pytest.ini              # pytest配置
│   ├── test_plan.md            # 测试计划
│   ├── test_cases/             # 测试用例
│   │   ├── test_auth.py
│   │   ├── test_users.py
│   │   ├── test_assessments.py
│   │   ├── test_conversations.py
│   │   ├── test_subscriptions.py
│   │   └── __init__.py
│   └── utils/                  # 测试工具
│       ├── test_client.py
│       └── __init__.py
│
├── doc/                        # 项目文档
│   ├── design.md               # 系统设计文档
│   ├── api.md                  # API接口文档
│   ├── database.md             # 数据库文档
│   ├── ui-design.md            # UI设计规范
│   ├── page-design.md          # 页面设计文档
│   ├── DEPLOY.md               # 部署指南
│   ├── changelog.md            # 变更日志
│   └── data_consistency.md     # 数据一致性文档
│
├── Dockerfile                  # Docker镜像定义
├── docker-compose.yml          # Docker Compose配置
├── nginx.conf                  # Nginx配置文件
├── redis.conf                  # Redis配置文件
├── start.sh                    # 服务启动脚本
├── stop.sh                     # 服务停止脚本
├── .env.example                # 环境变量示例
└── README.md                   # 项目说明文档
```

---

## 构建和运行命令

### Docker部署（推荐）

```bash
# 一键启动所有服务
./start.sh

# 强制重新构建镜像
./start.sh --build

# 跳过镜像构建
./start.sh --skip-build

# 启动并显示日志
./start.sh --logs

# 停止服务
./stop.sh
```

### 本地开发

```bash
# 1. 安装后端依赖
cd backend
pip install -r requirements.txt

# 2. 配置环境变量
cp .env.example .env
# 编辑 .env 文件配置必要参数

# 3. 初始化数据库
python -c "from database.connection import init_db; init_db()"

# 4. 启动后端服务
python main.py
# 或使用 uvicorn
uvicorn main:app --reload --host 0.0.0.0 --port 8000

# 5. 前端开发服务器
cd frontend
npm install
npm run dev  # 启动 http-server 在 3000 端口
```

### 服务访问地址

| 服务 | URL | 说明 |
|------|-----|------|
| 前端页面 | http://localhost | Nginx 默认80端口 |
| API接口 | http://localhost/api | 通过Nginx代理 |
| API文档 | http://localhost:8000/docs | FastAPI自动生成 |
| 健康检查 | http://localhost/health | 服务状态检查 |

---

## 测试命令

```bash
# 运行所有测试
pytest tests/

# 运行特定模块测试
pytest tests/test_cases/test_auth.py

# 运行特定标记的测试
pytest -m "auth"
pytest -m "not slow"

# 生成测试报告
pytest --html=report.html

# 显示详细输出
pytest -v

# 开启调试模式
pytest --pdb
```

### 测试标记 (Markers)

- `slow`: 慢速测试
- `integration`: 集成测试
- `auth`: 认证相关测试
- `api`: API接口测试
- `unit`: 单元测试

---

## 环境变量配置

项目使用 `.env` 文件管理配置，关键环境变量：

### 安全配置（生产环境必须修改）

```env
JWT_SECRET_KEY=your-super-secret-key-change-this-in-production
JWT_ALGORITHM=HS256
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=30
JWT_REFRESH_TOKEN_EXPIRE_DAYS=7
```

### AI服务配置（至少配置一个）

```env
OPENAI_API_KEY=sk-your-openai-api-key
OPENAI_BASE_URL=https://api.openai.com/v1
LLM_MODEL=gpt-4o-mini
LLM_TEMPERATURE=0.7
LLM_MAX_TOKENS=2000

# 可选：Anthropic Claude
ANTHROPIC_API_KEY=
```

### 数据库配置

```env
DATABASE_URL=sqlite:///data/ai_coach.db
DATABASE_POOL_SIZE=10
```

### 业务配置

```env
FREE_DAILY_CHAT_LIMIT=3
BASIC_DAILY_CHAT_LIMIT=20
PRO_DAILY_CHAT_LIMIT=-1  # -1表示无限
```

---

## 代码风格指南

### Python 代码规范

1. **编码声明**: 所有Python文件必须包含UTF-8编码声明
   ```python
   # -*- coding: utf-8 -*-
   ```

2. **文档字符串**: 使用中文编写模块、类和函数的文档字符串
   ```python
   """
   函数功能简要说明
   
   详细说明...
   
   Args:
       param1: 参数1说明
       param2: 参数2说明
       
   Returns:
       返回值说明
       
   Raises:
       Exception: 异常说明
   """
   ```

3. **命名规范**:
   - 模块名：小写，下划线分隔 (`auth_service.py`)
   - 类名：PascalCase (`AuthService`)
   - 函数/变量：snake_case (`get_user_by_id`)
   - 常量：UPPER_SNAKE_CASE (`MAX_RETRY_COUNT`)

4. **导入顺序**:
   1. 标准库
   2. 第三方库
   3. 项目内部模块

5. **类型注解**: 推荐使用类型注解
   ```python
   from typing import Optional, Dict, Any
   
   def get_user(user_id: int) -> Optional[Dict[str, Any]]:
       ...
   ```

### JavaScript 代码规范

1. **使用 ES6+ 语法**
2. **使用 JSDoc 注释**
3. **异步处理使用 async/await**

---

## 数据库规范

### ORM 模型定义

使用 SQLAlchemy 2.0 语法，模型文件位于 `backend/database/models.py`：

```python
from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy.orm import DeclarativeBase, relationship
from sqlalchemy.sql import func

class Base(DeclarativeBase):
    pass

class User(Base):
    """用户模型"""
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    email = Column(String(255), unique=True, nullable=False)
    created_at = Column(DateTime, default=func.current_timestamp())
```

### 数据库Schema

数据库初始化脚本：`backend/database/schema.sql`

包含：
- 8个主要表模块（用户、对话、测评、目标、订阅、知识库、系统、通知）
- 完整的索引定义
- 触发器（自动更新 updated_at）
- 初始数据（VIA 24种优势定义、教练提示词模板）

---

## API 设计规范

### 接口路径规范

```
/api/v1/auth/*          # 认证相关
/api/v1/users/*         # 用户管理
/api/v1/assessments/*   # 测评系统
/api/v1/conversations/* # 对话系统
/api/v1/subscriptions/* # 订阅管理
```

### 响应格式

统一响应结构：

```json
{
  "code": 200,
  "message": "操作成功",
  "data": { ... },
  "timestamp": "2024-01-15T10:30:00Z"
}
```

### 错误码规范

| 错误码范围 | 说明 |
|------------|------|
| 1000-1999 | 认证相关错误 |
| 2000-2999 | 测评相关错误 |
| 3000-3999 | 对话相关错误 |
| 4000-4999 | 订阅相关错误 |
| 5000-5999 | 系统错误 |

---

## 安全注意事项

### 生产环境安全清单

1. **JWT密钥**: 必须使用强随机字符串（建议32字节以上）
   ```bash
   openssl rand -hex 32
   ```

2. **API密钥**: 不要提交到代码仓库，使用 `.env` 文件管理

3. **文件权限**: 
   ```bash
   chmod 600 .env
   ```

4. **CORS配置**: 生产环境不要设置为 `*`

5. **密码安全**: 
   - 使用 bcrypt 加密
   - 最小长度6位，最大20位
   - 默认加密轮数12轮

6. **Nginx安全**: 
   - 启用HTTPS（SSL证书）
   - 配置速率限制
   - 添加安全响应头

---

## 常用开发任务

### 添加新的API接口

1. 在 `backend/routers/` 创建或修改路由文件
2. 定义请求/响应模型（使用 Pydantic）
3. 实现业务逻辑
4. 在 `main.py` 注册路由
5. 添加测试用例

### 添加数据库表

1. 在 `backend/database/models.py` 定义ORM模型
2. 在 `backend/database/schema.sql` 添加建表SQL
3. 如有需要，添加初始数据
4. 更新数据库版本（如使用迁移工具）

### 添加业务服务

1. 在 `backend/services/` 创建服务文件
2. 实现服务类和核心方法
3. 在 `services/__init__.py` 导出
4. 在 `main.py` 生命周期中初始化（如需要）

---

## 文档索引

| 文档 | 路径 | 说明 |
|------|------|------|
| 项目说明 | `README.md` | 项目简介和快速开始 |
| API文档 | `doc/api.md` | 详细接口定义 |
| 数据库文档 | `doc/database.md` | 数据模型说明 |
| 部署指南 | `doc/DEPLOY.md` | Docker部署步骤 |
| 设计文档 | `doc/design.md` | 系统架构设计 |
| UI设计 | `doc/ui-design.md` | 视觉设计规范 |
| 测试计划 | `tests/test_plan.md` | 测试策略 |

---

## 开发提示

1. **启动顺序**: 使用 `./start.sh` 脚本自动处理依赖检查和启动顺序

2. **热重载**: 开发模式使用 `uvicorn --reload` 自动重载代码

3. **日志查看**: 
   ```bash
   docker compose logs -f backend
   docker compose logs -f nginx
   ```

4. **数据库查看**: SQLite数据库文件位于 `./data/ai_coach.db`

5. **API测试**: 访问 `http://localhost:8000/docs` 使用Swagger UI测试接口

---

*最后更新: 2024年*
