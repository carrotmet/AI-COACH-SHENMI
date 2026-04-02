# 深觅 AI Coach - 优势教练系统

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.10+-blue.svg" alt="Python">
  <img src="https://img.shields.io/badge/FastAPI-0.100+-green.svg" alt="FastAPI">
  <img src="https://img.shields.io/badge/SQLite-3.0+-orange.svg" alt="SQLite">
  <img src="https://img.shields.io/badge/License-MIT-yellow.svg" alt="License">
</p>

## 项目简介

**深觅 AI Coach** 是一个基于优势教练理论的AI对话系统，帮助用户发现和发展个人优势，实现自我成长。

### 核心理念

- **优势导向**：基于VIA品格优势理论，聚焦优势发展而非短板弥补
- **AI赋能**：利用大语言模型提供个性化教练对话
- **科学方法**：整合积极心理学、GROW模型、DAIC框架
- **百年愿景**：构建可持续的人类发展支持系统

### 阶段一 MVP 功能

| 模块 | 功能描述 |
|------|----------|
| 用户认证 | 注册、登录、JWT Token认证 |
| 心理测评 | VIA品格优势评估（24题简化版） |
| AI对话 | 基于LazyLLM的优势教练对话 |
| 订阅管理 | 免费/付费订阅等级 |
| 用户中心 | 个人资料、历史记录、设置 |

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

## 技术栈

### 后端
- **框架**: FastAPI (Python 3.10+)
- **数据库**: SQLite + SQLAlchemy 2.0
- **认证**: JWT Token (python-jose)
- **AI**: LazyLLM + OpenAI/Claude API
- **部署**: Docker + Docker Compose

### 前端
- **技术**: 原生 JavaScript (ES6+)
- **样式**: CSS3 + 响应式设计
- **UI组件**: 自定义组件库

## 快速开始

### 方式一：Docker部署（推荐）

```bash
# 1. 克隆项目
cd /mnt/okcomputer/output

# 2. 配置环境变量
cp .env.example .env
vim .env  # 编辑配置

# 3. 启动服务
./start.sh

# 4. 访问服务
# 前端: http://localhost
# API文档: http://localhost:8000/docs
```

### 方式二：本地开发

```bash
# 1. 安装后端依赖
cd backend
pip install -r requirements.txt

# 2. 配置环境变量
cp .env.example .env
vim .env

# 3. 初始化数据库
python -c "from database.connection import init_db; init_db()"

# 4. 启动后端服务
python main.py

# 5. 前端直接打开
# 使用浏览器打开 frontend/index.html
```

## 项目结构

```
.
├── backend/                    # 后端代码
│   ├── main.py                 # FastAPI入口
│   ├── config.py               # 配置管理
│   ├── requirements.txt        # Python依赖
│   ├── database/               # 数据库模块
│   │   ├── models.py           # ORM模型
│   │   ├── connection.py       # 数据库连接
│   │   └── schema.sql          # 建表脚本
│   ├── routers/                # API路由
│   │   ├── auth.py             # 认证路由
│   │   ├── users.py            # 用户路由
│   │   ├── assessments.py      # 测评路由
│   │   ├── conversations.py    # 对话路由
│   │   └── subscriptions.py    # 订阅路由
│   ├── services/               # 业务服务
│   │   ├── chat_service.py     # 对话服务
│   │   ├── llm_service.py      # LLM服务
│   │   ├── assessment_service.py # 测评服务
│   │   ├── scoring_engine.py   # 评分引擎
│   │   └── report_service.py   # 报表服务
│   ├── utils/                  # 工具模块
│   │   ├── security.py         # 安全工具
│   │   └── response.py         # 响应格式
│   └── data/                   # 数据文件
│       ├── via_questions.py    # VIA测评题目
│       └── strength_data.py    # 优势定义
│
├── frontend/                   # 前端代码
│   ├── index.html              # 首页
│   ├── login.html              # 登录页
│   ├── register.html           # 注册页
│   ├── assessment/             # 测评页面
│   ├── chat/                   # 对话页面
│   ├── user/                   # 用户中心
│   ├── js/                     # JavaScript
│   └── styles/                 # CSS样式
│
├── tests/                      # 测试代码
│   ├── test_cases/             # 测试用例
│   └── test_plan.md            # 测试计划
│
├── doc/                        # 文档
│   ├── design.md               # 设计文档
│   ├── api.md                  # API文档
│   ├── database.md             # 数据库文档
│   ├── ui-design.md            # UI设计文档
│   └── DEPLOY.md               # 部署文档
│
├── Dockerfile                  # Docker镜像
├── docker-compose.yml          # Docker Compose
├── nginx.conf                  # Nginx配置
├── start.sh                    # 启动脚本
└── stop.sh                     # 停止脚本
```

## API文档

启动服务后访问: http://localhost:8000/docs

### 核心接口

| 接口 | 方法 | 路径 | 说明 |
|------|------|------|------|
| 用户注册 | POST | /api/v1/auth/register | 邮箱+密码注册 |
| 用户登录 | POST | /api/v1/auth/login | 邮箱+密码登录 |
| 创建测评 | POST | /api/v1/assessments | 创建VIA测评 |
| 提交答案 | POST | /api/v1/assessments/{id}/answers | 提交测评答案 |
| 获取结果 | GET | /api/v1/assessments/{id}/result | 获取测评结果 |
| 创建对话 | POST | /api/v1/conversations | 创建AI对话 |
| 发送消息 | POST | /api/v1/conversations/{id}/messages | 发送消息 |

## 核心功能

### 1. VIA品格优势评估

基于积极心理学的VIA（Values in Action）品格优势分类，评估用户的24种性格优势：

- **智慧与知识**: 好奇心、热爱学习、判断力、创造力、洞察力
- **勇气**: 勇敢、坚韧、正直、活力
- **人道**: 爱与被爱、善良、社交智慧
- **正义**: 团队合作、公平、领导力
- **节制**: 宽恕、谦逊、审慎、自我调节
- **超越**: 美感、感恩、希望、幽默、信仰

### 2. AI优势教练对话

基于LazyLLM框架，提供个性化的优势教练对话：

- **GROW模型**: Goal（目标）- Reality（现状）- Options（选择）- Will（意愿）
- **情感识别**: 自动识别用户情绪，提供共情回应
- **长期记忆**: 记住用户偏好和历史对话
- **个性化建议**: 基于优势档案提供针对性建议

### 3. 用户转化漏斗

```
免费测评 → 引流报表 → AI对话体验 → 付费订阅
```

## 配置说明

### 环境变量 (.env)

```env
# 应用配置
APP_NAME=深觅 AI Coach
APP_ENV=development
DEBUG=true

# 数据库
DATABASE_URL=sqlite:///./data/ai_coach.db

# JWT配置
JWT_SECRET_KEY=your-secret-key-here
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=15
REFRESH_TOKEN_EXPIRE_DAYS=7

# LLM配置
OPENAI_API_KEY=your-openai-api-key
OPENAI_MODEL=gpt-4o-mini

# 可选：Claude配置
ANTHROPIC_API_KEY=your-anthropic-api-key
```

## 订阅计划

| 计划 | 价格 | 功能 |
|------|------|------|
| Free | 免费 | 基础测评、每日5条AI对话 |
| Basic | ¥29/月 | 完整测评、每日50条对话、深度报表 |
| Pro | ¥59/月 | 无限对话、全部功能、优先支持 |

## 测试

```bash
# 运行所有测试
pytest tests/

# 运行特定模块测试
pytest tests/test_cases/test_auth.py

# 生成测试报告
pytest --html=report.html
```

## 文档

- [设计文档](doc/design.md) - 系统架构和模块设计
- [API文档](doc/api.md) - 接口详细说明
- [数据库文档](doc/database.md) - 数据模型和建表脚本
- [UI设计文档](doc/ui-design.md) - 视觉设计规范
- [部署文档](doc/DEPLOY.md) - 部署指南

## 开发路线图

### 阶段一 (MVP) ✅
- [x] 用户认证系统
- [x] VIA优势测评
- [x] AI对话系统
- [x] 订阅管理

### 阶段二 (扩展)
- [ ] 更多教练类型（职业、关系、健康）
- [ ] 人类教练网络
- [ ] 企业B2B版本

### 阶段三 (平台)
- [ ] 开放生态
- [ ] 预测性干预
- [ ] 全球扩展

## 贡献指南

1. Fork 项目
2. 创建功能分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 创建 Pull Request

## 许可证

本项目采用 MIT 许可证 - 详见 [LICENSE](LICENSE) 文件

## 联系我们

- 邮箱: contact@shenxun.ai
- 官网: https://shenxun.ai

---

<p align="center">
  <strong>深觅 AI Coach</strong> - 发现你的优势，成就更好的自己
</p>
