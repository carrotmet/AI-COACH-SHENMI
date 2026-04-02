# 深觅 AI Coach - 项目设计文档

## 1. 项目概述

### 1.1 项目背景

深觅 AI Coach 是一款基于人工智能技术的个人成长教练平台，专注于帮助用户发现和发挥个人优势，实现自我成长。阶段一MVP聚焦于**优势教练（Strengths Coaching）**这一单一教练类型，构建完整的用户转化漏斗。

### 1.2 产品定位

- **目标用户**：25-40岁职场人士、自我成长追求者
- **核心价值**：通过科学的心理测评和AI对话，帮助用户发现优势、制定成长计划
- **商业模式**：免费测评引流 + AI对话留存 + 付费订阅转化

### 1.3 阶段一MVP目标

| 目标维度 | 具体指标 |
|---------|---------|
| 功能范围 | 单一教练类型（优势教练） |
| 核心流程 | 心理测评 → 引流报表 → AI对话 → 付费转化 |
| 技术验证 | 验证LazyLLM集成效果和对话质量 |
| 用户验证 | 验证付费转化漏斗的有效性 |

### 1.4 设计理念

- **DAIC框架**：Discover（发现）→ Analyze（分析）→ Implement（实施）→ Consolidate（巩固）
- **ICF标准**：遵循国际教练联盟的专业教练标准
- **用户中心**：以用户体验为核心，降低使用门槛

---

## 2. 整体架构设计

### 2.1 系统分层架构

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              表现层 (Presentation Layer)                      │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │   Web前端     │  │  测评页面    │  │  对话界面    │  │  报表展示    │      │
│  │  (Vue3)      │  │  (问卷组件)  │  │  (聊天UI)   │  │  (可视化)   │      │
│  └──────────────┘  └──────────────┘  └──────────────┘  └──────────────┘      │
└─────────────────────────────────────────────────────────────────────────────┘
                                      │
                                      ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                              API网关层 (API Gateway)                         │
│  ┌──────────────────────────────────────────────────────────────────────┐  │
│  │                    FastAPI RESTful API 服务                           │  │
│  │  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐   │  │
│  │  │ 认证路由 │ │ 用户路由 │ │ 测评路由 │ │ 对话路由 │ │ 订阅路由 │   │  │
│  │  └──────────┘ └──────────┘ └──────────┘ └──────────┘ └──────────┘   │  │
│  └──────────────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────────────┘
                                      │
                                      ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                              业务逻辑层 (Business Layer)                      │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │  用户服务    │  │  测评服务    │  │  AI对话服务  │  │  订阅服务    │      │
│  │  User Svc   │  │ Assessment  │  │  Coaching   │  │ Subscription │      │
│  └──────────────┘  └──────────────┘  └──────────────┘  └──────────────┘      │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │  报表服务    │  │  通知服务    │  │  支付服务    │  │  分析服务    │      │
│  │  Report Svc │  │ Notification│  │  Payment    │  │  Analytics  │      │
│  └──────────────┘  └──────────────┘  └──────────────┘  └──────────────┘      │
└─────────────────────────────────────────────────────────────────────────────┘
                                      │
                                      ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                              数据访问层 (Data Access Layer)                   │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │  SQLAlchemy  │  │   Alembic    │  │   Redis      │  │   文件存储   │      │
│  │   ORM       │  │   迁移工具   │  │   缓存       │  │  (报表PDF)  │      │
│  └──────────────┘  └──────────────┘  └──────────────┘  └──────────────┘      │
└─────────────────────────────────────────────────────────────────────────────┘
                                      │
                                      ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                              数据存储层 (Data Storage Layer)                  │
│  ┌──────────────────────┐  ┌──────────────────────┐  ┌────────────────────┐ │
│  │      SQLite          │  │       Redis          │  │    文件系统        │ │
│  │  (主数据库)          │  │   (缓存/会话)        │  │  (静态资源/PDF)   │ │
│  └──────────────────────┘  └──────────────────────┘  └────────────────────┘ │
└─────────────────────────────────────────────────────────────────────────────┘
                                      │
                                      ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                              外部服务层 (External Services)                   │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │  LazyLLM     │  │  支付网关    │  │  短信服务    │  │  邮件服务    │      │
│  │  AI对话引擎  │  │  (Stripe/   │  │  (阿里云)   │  │  (SendGrid) │      │
│  │              │  │   微信支付) │  │             │  │             │      │
│  └──────────────┘  └──────────────┘  └──────────────┘  └──────────────┘      │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 2.2 核心数据流

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           用户转化漏斗数据流                                  │
└─────────────────────────────────────────────────────────────────────────────┘

[引流阶段]                    [留存阶段]                    [转化阶段]
    │                            │                            │
    ▼                            ▼                            ▼
┌─────────┐                ┌─────────┐                  ┌─────────┐
│ 用户访问 │ ────────────▶ │ 开始测评 │ ──────────────▶ │ 查看报表 │
│ 落地页  │                │ (VIA24) │                  │ (免费版) │
└─────────┘                └─────────┘                  └─────────┘
    │                            │                            │
    │                            │                            ▼
    │                            │                      ┌─────────┐
    │                            │                      │ 注册账号 │
    │                            │                      │ (手机号) │
    │                            │                      └─────────┘
    │                            │                            │
    │                            ▼                            ▼
    │                      ┌─────────┐                  ┌─────────┐
    │                      │ 完成测评 │ ──────────────▶ │ 解锁AI  │
    │                      │ 查看摘要 │                  │ 对话入口 │
    │                      └─────────┘                  └─────────┘
    │                            │                            │
    │                            │                            ▼
    │                            │                      ┌─────────┐
    │                            │                      │ AI优势  │
    │                            │                      │ 教练对话 │
    │                            │                      └─────────┘
    │                            │                            │
    │                            │                            ▼
    │                            │                      ┌─────────┐
    │                            │                      │ 免费对话 │
    │                            │                      │ 次数耗尽 │
    │                            │                      └─────────┘
    │                            │                            │
    │                            │                            ▼
    │                            │                      ┌─────────┐
    │                            │                      │ 引导付费 │
    │                            │                      │ 订阅会员 │
    │                            │                      └─────────┘
    │                            │                            │
    │                            │                            ▼
    │                            │                      ┌─────────┐
    │                            │                      │ 解锁无限 │
    │                            │                      │ 对话次数 │
    │                            │                      └─────────┘
    │                            │                            │
    ▼                            ▼                            ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                              数据持久化存储                                   │
│                    SQLite数据库 + Redis缓存 + 文件存储                        │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 2.3 模块依赖关系图

```
                         ┌─────────────────┐
                         │   API Gateway   │
                         │   (FastAPI)     │
                         └────────┬────────┘
                                  │
        ┌─────────────────────────┼─────────────────────────┐
        │                         │                         │
        ▼                         ▼                         ▼
┌───────────────┐        ┌───────────────┐        ┌───────────────┐
│   用户认证    │◀──────▶│   用户画像    │◀──────▶│   心理测评    │
│    Module     │        │    Module     │        │    Module     │
└───────┬───────┘        └───────┬───────┘        └───────┬───────┘
        │                        │                        │
        │                        │                        │
        │                        ▼                        │
        │               ┌───────────────┐                 │
        │               │   AI对话      │◀────────────────┘
        │               │   Module      │
        │               └───────┬───────┘
        │                       │
        │                       ▼
        │               ┌───────────────┐
        │               │   订阅管理    │
        │               │   Module      │
        │               └───────┬───────┘
        │                       │
        │                       ▼
        │               ┌───────────────┐
        └──────────────▶│   支付服务    │
                        │   Module      │
                        └───────────────┘

依赖说明：
- 实线箭头：直接依赖关系
- 虚线箭头：事件通知关系
- 所有模块都依赖：数据库层、配置管理、日志服务
```

---

## 3. 核心模块设计

### 3.1 用户认证模块 (Auth Module)

#### 3.1.1 功能职责

| 功能 | 说明 |
|-----|------|
| 用户注册 | 手机号+验证码注册 |
| 用户登录 | 手机号+验证码登录、JWT Token管理 |
| 密码管理 | 密码重置、修改密码 |
| 会话管理 | Token刷新、多设备登录控制 |
| 权限控制 | 基于角色的权限验证 |

#### 3.1.2 数据模型

```python
# 用户表 (users)
class User:
    id: int                    # 主键
    phone: str                 # 手机号（唯一）
    email: str                 # 邮箱（可选）
    password_hash: str         # 密码哈希
    nickname: str              # 昵称
    avatar_url: str            # 头像URL
    status: UserStatus         # 状态：active/inactive/banned
    role: UserRole             # 角色：user/admin
    created_at: datetime       # 创建时间
    updated_at: datetime       # 更新时间
    last_login_at: datetime    # 最后登录时间

# 用户认证表 (user_auth)
class UserAuth:
    id: int
    user_id: int               # 外键关联users
    auth_type: AuthType        # 认证类型：phone/wechat/apple
    auth_identifier: str       # 认证标识
    auth_credentials: str      # 认证凭证（加密存储）
    verified_at: datetime      # 验证时间

# 验证码表 (verification_codes)
class VerificationCode:
    id: int
    phone: str                 # 手机号
    code: str                  # 验证码
    purpose: CodePurpose       # 用途：register/login/reset
    expires_at: datetime       # 过期时间
    used_at: datetime          # 使用时间
```

#### 3.1.3 API接口

| 接口 | 方法 | 路径 | 说明 |
|-----|------|------|------|
| 发送验证码 | POST | /api/v1/auth/verify-code | 发送手机验证码 |
| 用户注册 | POST | /api/v1/auth/register | 手机号注册 |
| 用户登录 | POST | /api/v1/auth/login | 手机号+验证码登录 |
| Token刷新 | POST | /api/v1/auth/refresh | 刷新Access Token |
| 退出登录 | POST | /api/v1/auth/logout | 注销当前会话 |
| 重置密码 | POST | /api/v1/auth/reset-password | 重置密码 |

---

### 3.2 用户画像模块 (User Profile Module)

#### 3.2.1 功能职责

| 功能 | 说明 |
|-----|------|
| 基础信息管理 | 昵称、头像、性别、生日等 |
| 职业信息管理 | 职业、行业、工作年限等 |
| 目标管理 | 个人成长目标、期望成果 |
| 优势档案 | 关联测评结果，展示个人优势 |

#### 3.2.2 数据模型

```python
# 用户画像表 (user_profiles)
class UserProfile:
    id: int
    user_id: int               # 外键关联users
    
    # 基础信息
    gender: Gender             # 性别
    birthday: date             # 生日
    location: str              # 所在地区
    
    # 职业信息
    occupation: str            # 职业
    industry: str              # 行业
    work_years: int            # 工作年限
    company_scale: str         # 公司规模
    
    # 成长目标
    goals: List[str]           # 成长目标列表
    challenges: List[str]      # 当前挑战
    expectations: str          # 对教练的期望
    
    # 元数据
    created_at: datetime
    updated_at: datetime

# 优势档案表 (strength_profiles)
class StrengthProfile:
    id: int
    user_id: int               # 外键关联users
    assessment_id: int         # 关联的测评记录
    
    # 五大优势领域得分
    wisdom_score: float        # 智慧与知识
    courage_score: float       # 勇气
    humanity_score: float      # 人道主义
    justice_score: float       # 正义
    temperance_score: float    # 节制
    transcendence_score: float # 超越
    
    # 前5大优势（按得分排序）
    top_strengths: List[dict]  # [{"strength_id": 1, "name": "", "score": 0}]
    
    # 优势解读
    summary: str               # 优势总结
    recommendations: List[str] # 发展建议
    
    created_at: datetime
    updated_at: datetime
```

#### 3.2.3 API接口

| 接口 | 方法 | 路径 | 说明 |
|-----|------|------|------|
| 获取用户画像 | GET | /api/v1/users/profile | 获取当前用户画像 |
| 更新用户画像 | PUT | /api/v1/users/profile | 更新用户画像信息 |
| 获取优势档案 | GET | /api/v1/users/strengths | 获取用户优势档案 |
| 更新成长目标 | PUT | /api/v1/users/goals | 更新个人成长目标 |

---

### 3.3 心理测评模块 (Assessment Module)

#### 3.3.1 功能职责

| 功能 | 说明 |
|-----|------|
| 测评管理 | VIA优势测评问卷配置、题目管理 |
| 测评流程 | 开始测评、答题进度保存、提交测评 |
| 结果计算 | 优势维度得分计算、排名分析 |
| 报表生成 | 免费版摘要报表、付费版详细报表 |
| 历史记录 | 测评历史查询、结果对比 |

#### 3.3.2 VIA优势模型

```
VIA 24项性格优势分类（6大美德领域）：

┌─────────────────────────────────────────────────────────────────┐
│ 1. 智慧与知识 (Wisdom & Knowledge)                              │
│    - 创造力、好奇心、判断力、热爱学习、洞察力                    │
├─────────────────────────────────────────────────────────────────┤
│ 2. 勇气 (Courage)                                               │
│    - 勇敢、坚韧、正直、活力                                     │
├─────────────────────────────────────────────────────────────────┤
│ 3. 人道主义 (Humanity)                                          │
│    - 爱与被爱的能力、善良、社交智慧                             │
├─────────────────────────────────────────────────────────────────┤
│ 4. 正义 (Justice)                                               │
│    - 团队合作、公平、领导力                                     │
├─────────────────────────────────────────────────────────────────┤
│ 5. 节制 (Temperance)                                            │
│    - 宽恕、谦逊、谨慎、自我调节                                 │
├─────────────────────────────────────────────────────────────────┤
│ 6. 超越 (Transcendence)                                         │
│    - 审美、感恩、希望、幽默、灵性                               │
└─────────────────────────────────────────────────────────────────┘
```

#### 3.3.3 数据模型

```python
# 测评问卷表 (assessments)
class Assessment:
    id: int
    name: str                  # 测评名称
    code: str                  # 测评编码（如：VIA-24）
    description: str           # 测评描述
    type: AssessmentType       # 测评类型
    total_questions: int       # 总题数
    estimated_time: int        # 预计完成时间（分钟）
    status: AssessmentStatus   # 状态
    version: str               # 版本号
    created_at: datetime

# 测评题目表 (assessment_questions)
class AssessmentQuestion:
    id: int
    assessment_id: int         # 关联测评
    question_number: int       # 题号
    content: str               # 题目内容
    strength_id: int           # 关联的优势维度
    reverse_scored: bool       # 是否反向计分
    options: List[dict]        # 选项配置 [{"value": 1, "label": "非常不符合"}]

# 优势维度表 (strength_dimensions)
class StrengthDimension:
    id: int
    name: str                  # 优势名称
    name_en: str               # 英文名称
    category: str              # 所属美德领域
    description: str           # 优势描述
    characteristics: List[str] # 特征描述
    applications: List[str]    # 应用场景

# 用户测评记录表 (user_assessments)
class UserAssessment:
    id: int
    user_id: int               # 用户ID（未登录用户可为空）
    assessment_id: int         # 测评ID
    session_id: str            # 会话ID（用于未登录用户）
    
    # 进度信息
    status: AssessmentStatus   # 状态：in_progress/completed/abandoned
    current_question: int      # 当前题号
    answers: dict              # 答题记录 {question_id: answer_value}
    progress_percent: float    # 完成百分比
    
    # 结果信息
    started_at: datetime       # 开始时间
    completed_at: datetime     # 完成时间
    duration_seconds: int      # 耗时（秒）
    scores: dict               # 各维度得分
    report_generated: bool     # 报表是否已生成

# 测评报表表 (assessment_reports)
class AssessmentReport:
    id: int
    user_assessment_id: int    # 关联测评记录
    user_id: int               # 用户ID
    
    # 报表内容
    report_type: ReportType    # 报表类型：free/premium
    top_strengths: List[dict]  # 前5大优势详情
    dimension_scores: dict     # 各维度得分
    summary: str               # 总结分析
    recommendations: List[str] # 发展建议
    action_plans: List[str]    # 行动计划（付费版）
    
    # 文件存储
    pdf_url: str               # PDF报表URL
    
    created_at: datetime
```

#### 3.3.4 API接口

| 接口 | 方法 | 路径 | 说明 |
|-----|------|------|------|
| 获取测评列表 | GET | /api/v1/assessments | 获取可用测评列表 |
| 获取测评详情 | GET | /api/v1/assessments/{id} | 获取测评详情 |
| 开始测评 | POST | /api/v1/assessments/{id}/start | 开始新的测评 |
| 获取题目 | GET | /api/v1/assessments/{id}/questions | 获取测评题目 |
| 提交答案 | POST | /api/v1/assessments/{id}/answers | 提交答案 |
| 获取进度 | GET | /api/v1/assessments/{id}/progress | 获取答题进度 |
| 完成测评 | POST | /api/v1/assessments/{id}/complete | 完成测评 |
| 获取报表 | GET | /api/v1/assessments/{id}/report | 获取测评报表 |
| 下载PDF | GET | /api/v1/assessments/{id}/report/pdf | 下载PDF报表 |

---

### 3.4 AI对话模块 (AI Coaching Module)

#### 3.4.1 功能职责

| 功能 | 说明 |
|-----|------|
| 对话管理 | 创建对话、获取对话历史、删除对话 |
| 消息处理 | 发送消息、接收AI回复、消息存储 |
| 上下文管理 | 对话上下文维护、会话状态管理 |
| LazyLLM集成 | 调用LazyLLM进行AI对话生成 |
| 对话限制 | 免费用户对话次数限制、付费用户无限对话 |

#### 3.4.2 AI教练角色设定

```
优势教练（Strengths Coach）角色设定：

【角色身份】
你是一位专业的优势教练，基于VIA性格优势理论，帮助用户发现和发挥个人优势。

【核心能力】
1. 优势解读：根据用户的VIA测评结果，深入解读其前5大优势
2. 发展建议：针对用户的具体情况，提供个性化的优势发展建议
3. 目标规划：协助用户基于优势制定个人成长目标
4. 障碍突破：帮助用户识别并克服发挥优势的障碍
5. 行动指导：提供具体可行的行动计划和练习方法

【对话风格】
- 积极正向：聚焦优势而非弱点
- 启发引导：通过提问引导用户自我发现
- 专业可信：基于心理学理论和实践经验
- 温暖支持：给予情感支持和鼓励

【对话原则】
1. 遵循ICF教练标准，保持专业边界
2. 不提供医疗诊断或心理治疗
3. 尊重用户隐私，保护对话内容
4. 鼓励用户自主思考和决策
```

#### 3.4.3 数据模型

```python
# 对话会话表 (conversations)
class Conversation:
    id: int
    user_id: int               # 用户ID
    title: str                 # 对话标题
    
    # 对话配置
    coach_type: CoachType      # 教练类型：strengths
    context: dict              # 对话上下文（用户画像、测评结果等）
    
    # 状态管理
    status: ConversationStatus # 状态
    message_count: int         # 消息数量
    
    # 时间戳
    created_at: datetime
    updated_at: datetime
    last_message_at: datetime  # 最后消息时间

# 对话消息表 (conversation_messages)
class ConversationMessage:
    id: int
    conversation_id: int       # 关联对话
    
    # 消息内容
    role: MessageRole          # 角色：user/assistant/system
    content: str               # 消息内容
    content_type: str          # 内容类型：text/image
    
    # AI生成信息（仅assistant消息）
    model: str                 # 使用的模型
    tokens_used: int           # Token使用量
    generation_time: float     # 生成耗时（秒）
    
    # 元数据
    metadata: dict             # 额外元数据
    
    created_at: datetime

# 对话使用记录表 (conversation_usage)
class ConversationUsage:
    id: int
    user_id: int               # 用户ID
    conversation_id: int       # 对话ID
    
    # 使用量统计
    date: date                 # 日期
    message_count: int         # 当日消息数
    token_count: int           # 当日Token数
    
    # 限制信息
    limit_reached: bool        # 是否达到限制
    
    created_at: datetime
```

#### 3.4.4 LazyLLM集成设计

```python
# LazyLLM客户端封装
class LazyLLMClient:
    """
    LazyLLM AI对话客户端
    封装LazyLLM的调用，提供统一的对话接口
    """
    
    def __init__(self, api_key: str, base_url: str):
        self.api_key = api_key
        self.base_url = base_url
        self.client = lazyllm.Client(api_key=api_key, base_url=base_url)
    
    async def chat(
        self,
        messages: List[dict],
        system_prompt: str = None,
        temperature: float = 0.7,
        max_tokens: int = 2000
    ) -> dict:
        """
        发送对话请求
        
        Args:
            messages: 对话历史消息列表
            system_prompt: 系统提示词
            temperature: 温度参数
            max_tokens: 最大Token数
            
        Returns:
            {
                "content": "AI回复内容",
                "tokens_used": 150,
                "generation_time": 1.5
            }
        """
        pass
    
    def build_coach_prompt(
        self,
        user_profile: dict,
        strength_profile: dict,
        conversation_history: List[dict]
    ) -> str:
        """
        构建优势教练的系统提示词
        
        包含：
        1. 角色设定
        2. 用户画像信息
        3. 优势档案信息
        4. 对话指导原则
        """
        pass
```

#### 3.4.5 API接口

| 接口 | 方法 | 路径 | 说明 |
|-----|------|------|------|
| 创建对话 | POST | /api/v1/conversations | 创建新对话 |
| 获取对话列表 | GET | /api/v1/conversations | 获取用户对话列表 |
| 获取对话详情 | GET | /api/v1/conversations/{id} | 获取对话详情 |
| 删除对话 | DELETE | /api/v1/conversations/{id} | 删除对话 |
| 发送消息 | POST | /api/v1/conversations/{id}/messages | 发送消息 |
| 获取消息列表 | GET | /api/v1/conversations/{id}/messages | 获取对话消息 |
| 获取对话限制 | GET | /api/v1/conversations/limits | 获取当日对话限制 |

---

### 3.5 订阅管理模块 (Subscription Module)

#### 3.5.1 功能职责

| 功能 | 说明 |
|-----|------|
| 套餐管理 | 订阅套餐配置、价格管理 |
| 订阅管理 | 用户订阅状态查询、订阅升级/降级 |
| 权益管理 | 各等级权益配置、权益校验 |
| 支付集成 | 支付订单创建、支付回调处理 |
| 续费管理 | 自动续费、到期提醒 |

#### 3.5.2 订阅等级设计

```
┌─────────────────────────────────────────────────────────────────┐
│                        订阅等级体系                              │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  【免费版 Free】                                                  │
│  ├── 价格：¥0/月                                                 │
│  ├── VIA优势测评（完整版）                                        │
│  ├── 免费版测评报表（摘要）                                        │
│  ├── AI优势教练对话：3次/日                                       │
│  └── 对话历史保存：7天                                            │
│                                                                 │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  【基础版 Basic】¥29/月                                          │
│  ├── 包含免费版所有功能                                           │
│  ├── 完整版测评报表（PDF下载）                                     │
│  ├── AI优势教练对话：20次/日                                      │
│  ├── 对话历史保存：30天                                           │
│  └── 优先客服支持                                                 │
│                                                                 │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  【专业版 Pro】¥59/月                                            │
│  ├── 包含基础版所有功能                                           │
│  ├── AI优势教练对话：无限次数                                     │
│  ├── 对话历史保存：永久                                           │
│  ├── 专属成长计划                                                 │
│  ├── 优势发展练习库                                               │
│  └── 1对1教练咨询（每月1次）                                      │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

#### 3.5.3 数据模型

```python
# 订阅套餐表 (subscription_plans)
class SubscriptionPlan:
    id: int
    name: str                  # 套餐名称
    code: str                  # 套餐编码：free/basic/pro
    description: str           # 套餐描述
    
    # 价格配置
    price_monthly: Decimal     # 月付价格
    price_yearly: Decimal      # 年付价格
    currency: str              # 货币单位
    
    # 权益配置
    features: dict             # 权益详情
    daily_chat_limit: int      # 每日对话限制（-1表示无限）
    history_retention_days: int # 历史保存天数（-1表示永久）
    
    # 状态
    status: PlanStatus         # 状态
    sort_order: int            # 排序
    
    created_at: datetime

# 用户订阅表 (user_subscriptions)
class UserSubscription:
    id: int
    user_id: int               # 用户ID
    plan_id: int               # 套餐ID
    
    # 订阅信息
    status: SubscriptionStatus # 状态
    period: SubscriptionPeriod # 周期：monthly/yearly
    
    # 时间信息
    started_at: datetime       # 开始时间
    expires_at: datetime       # 过期时间
    canceled_at: datetime      # 取消时间
    
    # 支付信息
    payment_provider: str      # 支付渠道
    provider_subscription_id: str # 第三方订阅ID
    auto_renew: bool           # 是否自动续费
    
    created_at: datetime
    updated_at: datetime

# 支付订单表 (payment_orders)
class PaymentOrder:
    id: int
    order_no: str              # 订单号
    user_id: int               # 用户ID
    subscription_id: int       # 订阅ID
    
    # 订单信息
    plan_id: int               # 套餐ID
    period: SubscriptionPeriod # 周期
    amount: Decimal            # 金额
    currency: str              # 货币
    
    # 支付信息
    status: PaymentStatus      # 状态
    payment_provider: str      # 支付渠道
    provider_order_id: str     # 第三方订单ID
    paid_at: datetime          # 支付时间
    
    created_at: datetime
    updated_at: datetime
```

#### 3.5.4 API接口

| 接口 | 方法 | 路径 | 说明 |
|-----|------|------|------|
| 获取套餐列表 | GET | /api/v1/subscriptions/plans | 获取所有订阅套餐 |
| 获取当前订阅 | GET | /api/v1/subscriptions/current | 获取用户当前订阅 |
| 创建订单 | POST | /api/v1/subscriptions/orders | 创建支付订单 |
| 查询订单 | GET | /api/v1/subscriptions/orders/{id} | 查询订单状态 |
| 取消订阅 | POST | /api/v1/subscriptions/cancel | 取消自动续费 |
| 支付回调 | POST | /api/v1/subscriptions/webhook | 支付平台回调 |

---

### 3.6 管理后台模块 (Admin Module)

#### 3.6.1 功能职责

| 功能 | 说明 |
|-----|------|
| 用户管理 | 用户列表、用户详情、状态管理 |
| 数据统计 | 用户统计、测评统计、对话统计、转化漏斗 |
| 内容管理 | 测评题目管理、优势维度管理、提示词管理 |
| 订单管理 | 订单列表、退款处理、对账 |
| 系统配置 | 参数配置、通知模板、日志查看 |

#### 6.2 数据看板指标

```
┌─────────────────────────────────────────────────────────────────┐
│                        数据看板指标                              │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  【用户指标】                                                     │
│  ├── 总注册用户数                                                │
│  ├── 日新增用户数                                                │
│  ├── 活跃用户（DAU/MAU）                                         │
│  └── 用户留存率（次日/7日/30日）                                  │
│                                                                 │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  【测评指标】                                                     │
│  ├── 测评开始数                                                  │
│  ├── 测评完成数                                                  │
│  ├── 测评完成率                                                  │
│  └── 平均完成时间                                                │
│                                                                 │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  【对话指标】                                                     │
│  ├── 对话发起数                                                  │
│  ├── 消息发送数                                                  │
│  ├── 平均对话轮次                                                │
│  └── AI响应成功率                                                │
│                                                                 │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  【转化指标】                                                     │
│  ├── 注册转化率（测评完成→注册）                                  │
│  ├── 对话转化率（注册→首次对话）                                  │
│  ├── 付费转化率（对话→付费）                                      │
│  ├── ARPU（用户平均收入）                                         │
│  └── MRR（月度经常性收入）                                        │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## 4. 技术选型说明

### 4.1 技术栈总览

| 层级 | 技术选型 | 选型理由 |
|-----|---------|---------|
| 后端框架 | FastAPI | 高性能、异步支持、自动API文档、类型提示 |
| 数据库 | SQLite | MVP阶段轻量级选择，便于部署和迁移 |
| ORM | SQLAlchemy 2.0 | 成熟的Python ORM，支持异步 |
| 缓存 | Redis | 会话管理、限流、热点数据缓存 |
| AI引擎 | LazyLLM | 产品指定技术栈，支持多种模型 |
| 前端 | Vue3 + TypeScript | 现代化前端框架，类型安全 |
| 部署 | Docker + Nginx | 容器化部署，便于扩展 |

### 4.2 核心依赖

```python
# requirements.txt

# Web框架
fastapi==0.109.0
uvicorn[standard]==0.27.0
python-multipart==0.0.6

# 数据库
sqlalchemy[asyncio]==2.0.25
aiosqlite==0.19.0
alembic==1.13.1

# 缓存
redis==5.0.1

# 认证安全
python-jose[cryptography]==3.3.0
passlib[bcrypt]==1.7.4
python-dotenv==1.0.0

# AI集成
lazyllm==0.2.0

# 工具库
pydantic==2.5.3
pydantic-settings==2.1.0
httpx==0.26.0

# 任务队列（后续扩展）
celery==5.3.6

# 监控日志
structlog==24.1.0
prometheus-client==0.19.0
```

### 4.3 项目目录结构

```
shenxunmi-ai-coach/
├── app/
│   ├── __init__.py
│   ├── main.py                 # FastAPI应用入口
│   ├── config.py               # 配置管理
│   ├── dependencies.py         # 依赖注入
│   │
│   ├── api/                    # API路由层
│   │   ├── __init__.py
│   │   ├── v1/
│   │   │   ├── __init__.py
│   │   │   ├── auth.py         # 认证相关接口
│   │   │   ├── users.py        # 用户相关接口
│   │   │   ├── assessments.py  # 测评相关接口
│   │   │   ├── conversations.py # 对话相关接口
│   │   │   ├── subscriptions.py # 订阅相关接口
│   │   │   └── admin.py        # 管理后台接口
│   │   └── deps.py             # 路由依赖
│   │
│   ├── core/                   # 核心模块
│   │   ├── __init__.py
│   │   ├── security.py         # 安全工具（JWT、密码）
│   │   ├── exceptions.py       # 自定义异常
│   │   └── middleware.py       # 中间件
│   │
│   ├── models/                 # 数据模型层
│   │   ├── __init__.py
│   │   ├── base.py             # 基础模型
│   │   ├── user.py             # 用户模型
│   │   ├── assessment.py       # 测评模型
│   │   ├── conversation.py     # 对话模型
│   │   └── subscription.py     # 订阅模型
│   │
│   ├── schemas/                # Pydantic模型层
│   │   ├── __init__.py
│   │   ├── user.py             # 用户相关Schema
│   │   ├── auth.py             # 认证相关Schema
│   │   ├── assessment.py       # 测评相关Schema
│   │   ├── conversation.py     # 对话相关Schema
│   │   └── subscription.py     # 订阅相关Schema
│   │
│   ├── services/               # 业务逻辑层
│   │   ├── __init__.py
│   │   ├── user_service.py     # 用户服务
│   │   ├── auth_service.py     # 认证服务
│   │   ├── assessment_service.py # 测评服务
│   │   ├── conversation_service.py # 对话服务
│   │   ├── ai_service.py       # AI对话服务
│   │   └── subscription_service.py # 订阅服务
│   │
│   ├── crud/                   # 数据访问层
│   │   ├── __init__.py
│   │   ├── base.py             # 基础CRUD
│   │   ├── user.py             # 用户CRUD
│   │   ├── assessment.py       # 测评CRUD
│   │   └── conversation.py     # 对话CRUD
│   │
│   ├── db/                     # 数据库相关
│   │   ├── __init__.py
│   │   ├── session.py          # 数据库会话
│   │   └── base_class.py       # 基础类
│   │
│   ├── ai/                     # AI相关
│   │   ├── __init__.py
│   │   ├── lazyllm_client.py   # LazyLLM客户端
│   │   ├── prompts.py          # 提示词模板
│   │   └── coach_persona.py    # 教练角色设定
│   │
│   └── utils/                  # 工具函数
│       ├── __init__.py
│       ├── validators.py       # 验证工具
│       ├── formatters.py       # 格式化工具
│       └── datetime_utils.py   # 时间工具
│
├── alembic/                    # 数据库迁移
│   ├── versions/
│   └── env.py
│
├── tests/                      # 测试代码
│   ├── __init__.py
│   ├── conftest.py
│   ├── test_auth.py
│   ├── test_assessment.py
│   └── test_conversation.py
│
├── scripts/                    # 脚本工具
│   └── init_db.py
│
├── docs/                       # 文档
│   └── design.md
│
├── .env                        # 环境变量
├── .env.example                # 环境变量示例
├── requirements.txt            # 依赖列表
├── alembic.ini                 # Alembic配置
├── pytest.ini                 # Pytest配置
└── README.md                   # 项目说明
```

---

## 5. 接口设计原则

### 5.1 RESTful API规范

```
【URL设计】
- 使用名词复数形式：/api/v1/users, /api/v1/assessments
- 资源层级关系：/api/v1/users/{id}/profile
- 动作使用动词：/api/v1/auth/login, /api/v1/assessments/{id}/start

【HTTP方法】
- GET：获取资源
- POST：创建资源
- PUT：完整更新资源
- PATCH：部分更新资源
- DELETE：删除资源

【状态码】
- 200 OK：请求成功
- 201 Created：资源创建成功
- 400 Bad Request：请求参数错误
- 401 Unauthorized：未认证
- 403 Forbidden：无权限
- 404 Not Found：资源不存在
- 422 Unprocessable Entity：验证错误
- 500 Internal Server Error：服务器错误
```

### 5.2 统一响应格式

```python
# 成功响应
{
    "code": 200,
    "message": "success",
    "data": {
        # 具体数据
    }
}

# 列表响应
{
    "code": 200,
    "message": "success",
    "data": {
        "items": [...],
        "total": 100,
        "page": 1,
        "page_size": 20
    }
}

# 错误响应
{
    "code": 400,
    "message": "请求参数错误",
    "error": {
        "field": "phone",
        "detail": "手机号格式不正确"
    }
}
```

### 5.3 认证机制

```
【JWT Token机制】
1. 登录成功后，服务端返回 Access Token 和 Refresh Token
2. Access Token 有效期：2小时
3. Refresh Token 有效期：7天
4. 请求时在 Header 中携带：Authorization: Bearer {token}

【Token刷新流程】
1. 客户端检测到 Access Token 即将过期
2. 使用 Refresh Token 调用 /api/v1/auth/refresh
3. 服务端验证 Refresh Token 有效后，返回新的 Token 对
4. 如果 Refresh Token 也过期，需要重新登录
```

### 5.4 模块间接口契约

```python
# ==================== 用户认证模块接口 ====================

class AuthServiceInterface:
    """认证服务接口定义"""
    
    async def send_verification_code(self, phone: str, purpose: str) -> bool:
        """发送验证码"""
        pass
    
    async def verify_code(self, phone: str, code: str, purpose: str) -> bool:
        """验证验证码"""
        pass
    
    async def register(self, phone: str, code: str, password: str) -> User:
        """用户注册"""
        pass
    
    async def login(self, phone: str, code: str = None, password: str = None) -> TokenPair:
        """用户登录"""
        pass
    
    async def refresh_token(self, refresh_token: str) -> TokenPair:
        """刷新Token"""
        pass

# ==================== 用户画像模块接口 ====================

class UserProfileServiceInterface:
    """用户画像服务接口定义"""
    
    async def get_profile(self, user_id: int) -> UserProfile:
        """获取用户画像"""
        pass
    
    async def update_profile(self, user_id: int, data: dict) -> UserProfile:
        """更新用户画像"""
        pass
    
    async def get_strength_profile(self, user_id: int) -> StrengthProfile:
        """获取优势档案"""
        pass

# ==================== 心理测评模块接口 ====================

class AssessmentServiceInterface:
    """测评服务接口定义"""
    
    async def start_assessment(self, user_id: int, assessment_id: int) -> UserAssessment:
        """开始测评"""
        pass
    
    async def submit_answer(self, user_assessment_id: int, question_id: int, answer: int) -> dict:
        """提交答案"""
        pass
    
    async def complete_assessment(self, user_assessment_id: int) -> AssessmentReport:
        """完成测评并生成报表"""
        pass
    
    async def get_report(self, user_assessment_id: int, report_type: str) -> AssessmentReport:
        """获取测评报表"""
        pass

# ==================== AI对话模块接口 ====================

class ConversationServiceInterface:
    """对话服务接口定义"""
    
    async def create_conversation(self, user_id: int, context: dict) -> Conversation:
        """创建对话"""
        pass
    
    async def send_message(self, conversation_id: int, content: str) -> Message:
        """发送消息并获取AI回复"""
        pass
    
    async def get_conversation_history(self, conversation_id: int) -> List[Message]:
        """获取对话历史"""
        pass
    
    async def check_chat_limit(self, user_id: int) -> dict:
        """检查对话限制"""
        pass

# ==================== AI服务模块接口 ====================

class AIServiceInterface:
    """AI服务接口定义"""
    
    async def chat(
        self,
        messages: List[dict],
        user_context: dict,
        temperature: float = 0.7
    ) -> dict:
        """AI对话"""
        pass
    
    def build_coach_context(self, user_profile: dict, strength_profile: dict) -> str:
        """构建教练上下文"""
        pass

# ==================== 订阅管理模块接口 ====================

class SubscriptionServiceInterface:
    """订阅服务接口定义"""
    
    async def get_current_subscription(self, user_id: int) -> UserSubscription:
        """获取当前订阅"""
        pass
    
    async def create_order(self, user_id: int, plan_id: int, period: str) -> PaymentOrder:
        """创建支付订单"""
        pass
    
    async def process_payment_callback(self, provider: str, data: dict) -> bool:
        """处理支付回调"""
        pass
    
    async def check_feature_access(self, user_id: int, feature: str) -> bool:
        """检查功能访问权限"""
        pass
```

---

## 6. 开发计划与里程碑

### 6.1 项目里程碑

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                          项目里程碑规划                                      │
└─────────────────────────────────────────────────────────────────────────────┘

Week 1-2: 基础架构搭建
├── Day 1-3: 项目初始化、环境配置、数据库设计
├── Day 4-5: 用户认证模块开发
├── Day 6-7: 用户画像模块开发
└── 里程碑1: 用户系统可用

Week 3-4: 核心功能开发
├── Day 8-10: 心理测评模块开发
├── Day 11-12: 测评报表生成
├── Day 13-14: AI对话模块开发
└── 里程碑2: 测评+对话核心功能可用

Week 5: 商业化功能
├── Day 15-17: 订阅管理模块开发
├── Day 18-19: 支付集成
├── Day 20-21: 管理后台开发
└── 里程碑3: 付费转化漏斗完整

Week 6: 测试与优化
├── Day 22-24: 功能测试、Bug修复
├── Day 25-26: 性能优化
├── Day 27-28: 集成测试、UAT
└── 里程碑4: MVP版本发布就绪
```

### 6.2 详细任务分解

#### Phase 1: 基础架构（Week 1-2）

| 任务ID | 任务名称 | 负责人 | 预计工时 | 依赖 |
|-------|---------|-------|---------|------|
| P1-T1 | 项目初始化与环境配置 | 后端工程师 | 8h | - |
| P1-T2 | 数据库设计与模型定义 | 后端工程师 | 12h | P1-T1 |
| P1-T3 | 基础工具类开发 | 后端工程师 | 8h | P1-T1 |
| P1-T4 | 用户注册/登录接口 | 后端工程师 | 12h | P1-T2 |
| P1-T5 | JWT认证中间件 | 后端工程师 | 8h | P1-T4 |
| P1-T6 | 用户画像接口 | 后端工程师 | 10h | P1-T4 |
| P1-T7 | 前端基础框架搭建 | 前端工程师 | 16h | - |
| P1-T8 | 登录/注册页面 | 前端工程师 | 12h | P1-T7 |

#### Phase 2: 核心功能（Week 3-4）

| 任务ID | 任务名称 | 负责人 | 预计工时 | 依赖 |
|-------|---------|-------|---------|------|
| P2-T1 | VIA测评题目数据导入 | 后端工程师 | 8h | P1-T2 |
| P2-T2 | 测评流程接口开发 | 后端工程师 | 16h | P2-T1 |
| P2-T3 | 测评结果计算算法 | 后端工程师 | 12h | P2-T2 |
| P2-T4 | 免费版报表生成 | 后端工程师 | 16h | P2-T3 |
| P2-T5 | LazyLLM客户端封装 | AI工程师 | 12h | - |
| P2-T6 | AI对话接口开发 | AI工程师 | 16h | P2-T5 |
| P2-T7 | 对话上下文管理 | AI工程师 | 12h | P2-T6 |
| P2-T8 | 测评页面开发 | 前端工程师 | 20h | P1-T8 |
| P2-T9 | 报表展示页面 | 前端工程师 | 16h | P2-T8 |
| P2-T10 | 对话界面开发 | 前端工程师 | 20h | P2-T9 |

#### Phase 3: 商业化功能（Week 5）

| 任务ID | 任务名称 | 负责人 | 预计工时 | 依赖 |
|-------|---------|-------|---------|------|
| P3-T1 | 订阅套餐配置 | 后端工程师 | 8h | P1-T2 |
| P3-T2 | 订单管理接口 | 后端工程师 | 12h | P3-T1 |
| P3-T3 | 支付网关集成 | 后端工程师 | 16h | P3-T2 |
| P3-T4 | 权益校验逻辑 | 后端工程师 | 10h | P3-T3 |
| P3-T5 | 付费版报表生成 | 后端工程师 | 12h | P2-T4 |
| P3-T6 | 管理后台接口 | 后端工程师 | 16h | P3-T4 |
| P3-T7 | 订阅页面开发 | 前端工程师 | 16h | P2-T10 |
| P3-T8 | 管理后台界面 | 前端工程师 | 20h | P3-T7 |

#### Phase 4: 测试与优化（Week 6）

| 任务ID | 任务名称 | 负责人 | 预计工时 | 依赖 |
|-------|---------|-------|---------|------|
| P4-T1 | 单元测试编写 | 后端工程师 | 16h | P3-T6 |
| P4-T2 | 接口测试 | 后端工程师 | 12h | P4-T1 |
| P4-T3 | 集成测试 | 全团队 | 16h | P4-T2 |
| P4-T4 | 性能优化 | 后端工程师 | 12h | P4-T3 |
| P4-T5 | Bug修复 | 全团队 | 16h | P4-T3 |
| P4-T6 | 部署配置 | 后端工程师 | 8h | P4-T5 |
| P4-T7 | 文档完善 | 产品经理 | 12h | P4-T6 |

### 6.3 风险与应对

| 风险项 | 风险等级 | 应对措施 |
|-------|---------|---------|
| LazyLLM集成复杂度超预期 | 高 | 提前进行技术验证，准备备选方案 |
| 测评算法准确性争议 | 中 | 参考权威VIA量表，邀请心理学专家审核 |
| 支付集成延迟 | 中 | 优先使用沙箱环境开发，并行进行 |
| AI对话质量不达标 | 高 | 持续优化提示词，设置质量监控指标 |
| 性能瓶颈 | 中 | 提前设计缓存策略，准备性能测试方案 |

---

## 7. 附录

### 7.1 术语表

| 术语 | 说明 |
|-----|------|
| VIA | Values in Action，性格优势分类体系 |
| DAIC | Discover-Analyze-Implement-Consolidate，教练流程框架 |
| ICF | International Coach Federation，国际教练联盟 |
| MVP | Minimum Viable Product，最小可行产品 |
| JWT | JSON Web Token，认证令牌 |
| ORM | Object-Relational Mapping，对象关系映射 |
| DAU | Daily Active Users，日活跃用户 |
| MAU | Monthly Active Users，月活跃用户 |
| ARPU | Average Revenue Per User，用户平均收入 |
| MRR | Monthly Recurring Revenue，月度经常性收入 |

### 7.2 参考文档

- VIA性格优势官方文档
- ICF教练核心能力标准
- FastAPI官方文档
- LazyLLM开发文档
- RESTful API设计规范

---

**文档版本**: v1.0  
**创建日期**: 2024年  
**最后更新**: 2024年  
**文档状态**: 初稿
