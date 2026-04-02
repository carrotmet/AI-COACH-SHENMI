# 深觅 AI Coach - 数据库设计文档

> 版本: 1.0.0  
> 数据库: SQLite  
> 创建日期: 2024

---

## 目录

1. [概述](#概述)
2. [ER图设计](#er图设计)
3. [数据表结构](#数据表结构)
4. [索引设计](#索引设计)
5. [数据关系说明](#数据关系说明)
6. [SQL建表脚本](#sql建表脚本)

---

## 概述

### 设计目标

本数据库设计旨在支持"深觅 AI Coach"系统的核心功能：

- **用户管理**: 用户注册、认证、画像管理
- **对话系统**: 多轮对话存储、消息历史、上下文管理
- **评估系统**: VIA优势评估、心理测评、结果分析
- **目标管理**: 目标设定、里程碑追踪、进展记录
- **订阅系统**: 付费计划、配额管理、支付记录
- **知识库**: 教练知识、优势定义、提示词模板

### 设计原则

1. **ACID合规**: 确保数据一致性和完整性
2. **可扩展性**: JSON字段支持灵活数据结构
3. **性能优化**: 合理设计索引策略
4. **审计追踪**: 完整的操作日志记录
5. **隐私保护**: 支持数据脱敏和软删除

---

## ER图设计

### 实体关系图 (ASCII)

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           深觅 AI Coach 数据库 ER图                          │
└─────────────────────────────────────────────────────────────────────────────┘

┌──────────────┐       ┌─────────────────┐       ┌──────────────────┐
│    users     │◄──────┤  user_profiles  │       │   user_tokens    │
├──────────────┤  1:1  ├─────────────────┤       ├──────────────────┤
│ PK id        │       │ PK id           │       │ PK id            │
│ username     │       │ FK user_id      │       │ FK user_id       │
│ email        │       │ nickname        │       │ token_hash       │
│ password_hash│       │ strengths_profile│      │ expires_at       │
│ status       │       │ preferences     │       │ revoked          │
└──────┬───────┘       └─────────────────┘       └──────────────────┘
       │
       │ 1:N
       ▼
┌─────────────────────────────────────────────────────────────────┐
│                         核心业务表                                │
├──────────────┬──────────────┬──────────────┬──────────────────────┤
│              │              │              │                      │
│ ▼            │ ▼            │ ▼            │ ▼                    │ ▼
┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐          ┌──────────┐
│conversations│ │ messages │  │assessments│  │   goals  │          │subscriptions│
├──────────┤  ├──────────┤  ├──────────┤  ├──────────┤          ├──────────┤
│PK id     │  │PK id     │  │PK id     │  │PK id     │          │PK id     │
│FK user_id│  │FK conv_id│  │FK user_id│  │FK user_id│          │FK user_id│
│title     │  │role      │  │type      │  │title     │          │plan_type │
│status    │  │content   │  │status    │  │status    │          │status    │
│coach_type│  │emotion   │  │score_sum │  │deadline  │          │end_date  │
└────┬─────┘  └──────────┘  └────┬─────┘  └────┬─────┘          └──────────┘
     │                           │             │
     │                           │             │
     ▼                           ▼             ▼
┌─────────────────┐  ┌─────────────────────┐  ┌─────────────────┐
│conversation_    │  │ assessment_results  │  │ goal_milestones │
│summaries       │  ├─────────────────────┤  ├─────────────────┤
├─────────────────┤  │PK id                │  │PK id            │
│PK id            │  │FK assessment_id     │  │FK goal_id       │
│FK conversation_id│ │dimension_name       │  │title            │
│summary          │  │score                │  │status           │
│key_points       │  │percentile           │  │target_date      │
└─────────────────┘  └─────────────────────┘  └─────────────────┘
                            │
                            │
                            ▼
                     ┌─────────────────────┐
                     │assessment_responses │
                     ├─────────────────────┤
                     │PK id                │
                     │FK assessment_id     │
                     │question_id          │
                     │response_value       │
                     └─────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│                         支持系统表                                │
├──────────────┬──────────────┬──────────────┬──────────────────────┤
│              │              │              │                      │
│ ▼            │ ▼            │ ▼            │ ▼                    │ ▼
┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐          ┌──────────┐
│coach_    │  │strength_ │  │coach_    │  │usage_    │          │ payments │
│knowledge │  │definitions│ │prompts   │  │quotas    │          ├──────────┤
├──────────┤  ├──────────┤  ├──────────┤  ├──────────┤          │PK id     │
│PK id     │  │PK id     │  │PK id     │  │PK id     │          │FK user_id│
│category  │  │strength_ │  │prompt_   │  │FK user_id│          │amount    │
│topic     │  │key       │  │type      │  │plan_type │          │status    │
│content   │  │virtue_   │  │template  │  │quota_    │          │paid_at   │
│tags      │  │category  │  │is_default│  │limits    │          └──────────┘
└──────────┘  └──────────┘  └──────────┘  └──────────┘

┌─────────────────────────────────────────────────────────────────┐
│                         系统管理表                                │
├──────────────┬──────────────┬──────────────┬──────────────────────┤
│              │              │              │                      │
│ ▼            │ ▼            │ ▼            │ ▼                    │
┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐
│system_   │  │audit_    │  │app_      │  │notifications│
│configs   │  │logs      │  │logs      │  ├──────────┤
├──────────┤  ├──────────┤  ├──────────┤  │PK id     │
│PK id     │  │PK id     │  │PK id     │  │FK user_id│
│config_key│  │FK user_id│  │log_level │  │type      │
│config_val│  │action    │  │source    │  │title     │
│category  │  │entity_   │  │message   │  │is_read   │
└──────────┘  │type      │  └──────────┘  └──────────┘
              └──────────┘
```

### 核心实体关系说明

| 主表 | 关联表 | 关系类型 | 说明 |
|------|--------|----------|------|
| users | user_profiles | 1:1 | 每个用户有一个画像 |
| users | user_tokens | 1:N | 用户可在多设备登录 |
| users | conversations | 1:N | 用户有多个对话会话 |
| users | assessments | 1:N | 用户可进行多次评估 |
| users | goals | 1:N | 用户可设定多个目标 |
| users | subscriptions | 1:N | 用户可有多个订阅记录 |
| conversations | messages | 1:N | 会话包含多条消息 |
| conversations | conversation_summaries | 1:1 | 每个会话有一个摘要 |
| assessments | assessment_results | 1:N | 评估有多个维度结果 |
| assessments | assessment_responses | 1:N | 评估有多个答题记录 |
| goals | goal_milestones | 1:N | 目标有多个里程碑 |
| goals | goal_progress | 1:N | 目标有多条进展记录 |

---

## 数据表结构

### 1. 用户管理相关表

#### 1.1 users - 用户基础信息表

| 字段名 | 类型 | 约束 | 说明 |
|--------|------|------|------|
| id | INTEGER | PK, AUTOINCREMENT | 用户ID |
| username | VARCHAR(50) | UNIQUE, NOT NULL | 用户名 |
| email | VARCHAR(255) | UNIQUE, NOT NULL | 邮箱 |
| password_hash | VARCHAR(255) | NOT NULL | 密码哈希 |
| phone | VARCHAR(20) | UNIQUE | 手机号 |
| avatar_url | TEXT | - | 头像URL |
| status | VARCHAR(20) | DEFAULT 'active' | 状态: active/inactive/suspended/deleted |
| subscription_type | VARCHAR(20) | DEFAULT 'free' | 订阅类型: free/basic/premium/enterprise |
| email_verified | BOOLEAN | DEFAULT FALSE | 邮箱是否验证 |
| phone_verified | BOOLEAN | DEFAULT FALSE | 手机是否验证 |
| last_login_at | DATETIME | - | 最后登录时间 |
| created_at | DATETIME | DEFAULT CURRENT_TIMESTAMP | 创建时间 |
| updated_at | DATETIME | DEFAULT CURRENT_TIMESTAMP | 更新时间 |
| deleted_at | DATETIME | - | 软删除标记 |

#### 1.2 user_profiles - 用户画像表

| 字段名 | 类型 | 约束 | 说明 |
|--------|------|------|------|
| id | INTEGER | PK, AUTOINCREMENT | 画像ID |
| user_id | INTEGER | UNIQUE, NOT NULL, FK | 用户ID |
| nickname | VARCHAR(50) | - | 昵称 |
| gender | VARCHAR(10) | CHECK | 性别 |
| birth_date | DATE | - | 出生日期 |
| occupation | VARCHAR(100) | - | 职业 |
| company | VARCHAR(100) | - | 公司 |
| industry | VARCHAR(50) | - | 行业 |
| location | VARCHAR(100) | - | 所在地 |
| bio | TEXT | - | 个人简介 |
| goals | TEXT | - | 用户目标描述 |
| interests | TEXT | - | 兴趣爱好 |
| strengths_profile | JSON | - | 优势档案(34种优势评分) |
| personality_type | VARCHAR(10) | - | MBTI等性格类型 |
| preferences | JSON | - | 用户偏好设置 |
| coaching_style_preference | VARCHAR(20) | - | 教练风格偏好 |
| notification_settings | JSON | DEFAULT | 通知设置 |
| privacy_settings | JSON | DEFAULT | 隐私设置 |
| created_at | DATETIME | DEFAULT CURRENT_TIMESTAMP | 创建时间 |
| updated_at | DATETIME | DEFAULT CURRENT_TIMESTAMP | 更新时间 |

#### 1.3 user_tokens - 用户认证令牌表

| 字段名 | 类型 | 约束 | 说明 |
|--------|------|------|------|
| id | INTEGER | PK, AUTOINCREMENT | 令牌ID |
| user_id | INTEGER | NOT NULL, FK | 用户ID |
| token_type | VARCHAR(20) | NOT NULL, CHECK | 令牌类型 |
| token_hash | VARCHAR(255) | NOT NULL | 令牌哈希 |
| device_info | JSON | - | 设备信息 |
| ip_address | VARCHAR(45) | - | IP地址 |
| expires_at | DATETIME | NOT NULL | 过期时间 |
| created_at | DATETIME | DEFAULT CURRENT_TIMESTAMP | 创建时间 |
| last_used_at | DATETIME | - | 最后使用时间 |
| revoked | BOOLEAN | DEFAULT FALSE | 是否撤销 |

---

### 2. 对话系统相关表

#### 2.1 conversations - 对话会话表

| 字段名 | 类型 | 约束 | 说明 |
|--------|------|------|------|
| id | INTEGER | PK, AUTOINCREMENT | 会话ID |
| user_id | INTEGER | NOT NULL, FK | 用户ID |
| title | VARCHAR(200) | DEFAULT '新对话' | 会话标题 |
| status | VARCHAR(20) | DEFAULT 'active' | 状态: active/archived/deleted |
| coach_type | VARCHAR(30) | DEFAULT 'strength' | 教练类型 |
| context | JSON | - | 对话上下文 |
| metadata | JSON | - | 元数据 |
| message_count | INTEGER | DEFAULT 0 | 消息数量 |
| started_at | DATETIME | DEFAULT CURRENT_TIMESTAMP | 开始时间 |
| ended_at | DATETIME | - | 结束时间 |
| created_at | DATETIME | DEFAULT CURRENT_TIMESTAMP | 创建时间 |
| updated_at | DATETIME | DEFAULT CURRENT_TIMESTAMP | 更新时间 |

#### 2.2 messages - 消息记录表

| 字段名 | 类型 | 约束 | 说明 |
|--------|------|------|------|
| id | INTEGER | PK, AUTOINCREMENT | 消息ID |
| conversation_id | INTEGER | NOT NULL, FK | 会话ID |
| role | VARCHAR(20) | NOT NULL, CHECK | 角色: user/assistant/system/coach |
| content | TEXT | NOT NULL | 消息内容 |
| content_type | VARCHAR(20) | DEFAULT 'text' | 内容类型 |
| emotion_tag | VARCHAR(30) | - | 情绪标签 |
| sentiment_score | REAL | CHECK (-1 to 1) | 情感分数 |
| model_info | JSON | - | AI模型信息 |
| tokens_used | INTEGER | - | Token使用量 |
| response_time_ms | INTEGER | - | 响应时间(毫秒) |
| is_edited | BOOLEAN | DEFAULT FALSE | 是否编辑 |
| edited_at | DATETIME | - | 编辑时间 |
| parent_message_id | INTEGER | FK | 父消息ID |
| attachments | JSON | - | 附件信息 |
| metadata | JSON | - | 元数据 |
| created_at | DATETIME | DEFAULT CURRENT_TIMESTAMP | 创建时间 |

#### 2.3 conversation_summaries - 对话摘要表

| 字段名 | 类型 | 约束 | 说明 |
|--------|------|------|------|
| id | INTEGER | PK, AUTOINCREMENT | 摘要ID |
| conversation_id | INTEGER | UNIQUE, NOT NULL, FK | 会话ID |
| summary | TEXT | - | 摘要内容 |
| key_points | JSON | - | 关键要点 |
| action_items | JSON | - | 行动项 |
| topics | JSON | - | 讨论主题 |
| sentiment_overview | VARCHAR(50) | - | 情感概览 |
| generated_at | DATETIME | DEFAULT CURRENT_TIMESTAMP | 生成时间 |
| updated_at | DATETIME | DEFAULT CURRENT_TIMESTAMP | 更新时间 |

---

### 3. 评估系统相关表

#### 3.1 assessments - 评估记录表

| 字段名 | 类型 | 约束 | 说明 |
|--------|------|------|------|
| id | INTEGER | PK, AUTOINCREMENT | 评估ID |
| user_id | INTEGER | NOT NULL, FK | 用户ID |
| assessment_type | VARCHAR(30) | NOT NULL, CHECK | 评估类型 |
| title | VARCHAR(200) | - | 标题 |
| description | TEXT | - | 描述 |
| status | VARCHAR(20) | DEFAULT 'pending' | 状态 |
| version | VARCHAR(10) | DEFAULT '1.0' | 版本 |
| score_summary | JSON | - | 评分汇总 |
| interpretation | TEXT | - | 结果解读 |
| recommendations | JSON | - | 建议 |
| started_at | DATETIME | - | 开始时间 |
| completed_at | DATETIME | - | 完成时间 |
| valid_until | DATETIME | - | 有效期至 |
| created_at | DATETIME | DEFAULT CURRENT_TIMESTAMP | 创建时间 |
| updated_at | DATETIME | DEFAULT CURRENT_TIMESTAMP | 更新时间 |

**评估类型 (assessment_type)**:
- `via_strengths` - VIA性格优势评估
- `mbti` - MBTI性格测试
- `disc` - DISC行为风格
- `big_five` - 大五人格
- `custom` - 自定义评估
- `weekly_checkin` - 周度检查
- `goal_progress` - 目标进展评估

#### 3.2 assessment_results - 评估结果详情表

| 字段名 | 类型 | 约束 | 说明 |
|--------|------|------|------|
| id | INTEGER | PK, AUTOINCREMENT | 结果ID |
| assessment_id | INTEGER | NOT NULL, FK | 评估ID |
| dimension_name | VARCHAR(100) | NOT NULL | 维度名称 |
| dimension_code | VARCHAR(50) | - | 维度代码 |
| category | VARCHAR(50) | - | 所属类别 |
| score | REAL | NOT NULL | 原始分数 |
| normalized_score | REAL | - | 标准化分数(0-100) |
| percentile | INTEGER | CHECK (0-100) | 百分位 |
| rank | INTEGER | - | 排名 |
| interpretation | TEXT | - | 维度解读 |
| strengths_description | TEXT | - | 优势描述 |
| development_tips | TEXT | - | 发展建议 |
| related_strengths | JSON | - | 相关优势 |
| metadata | JSON | - | 元数据 |
| created_at | DATETIME | DEFAULT CURRENT_TIMESTAMP | 创建时间 |

#### 3.3 assessment_responses - 评估答题记录表

| 字段名 | 类型 | 约束 | 说明 |
|--------|------|------|------|
| id | INTEGER | PK, AUTOINCREMENT | 记录ID |
| assessment_id | INTEGER | NOT NULL, FK | 评估ID |
| question_id | VARCHAR(50) | NOT NULL | 问题ID |
| question_text | TEXT | - | 问题文本 |
| response_value | TEXT | NOT NULL | 回答值 |
| response_score | REAL | - | 评分 |
| response_time_ms | INTEGER | - | 答题用时 |
| created_at | DATETIME | DEFAULT CURRENT_TIMESTAMP | 创建时间 |

---

### 4. 目标管理相关表

#### 4.1 goals - 用户目标表

| 字段名 | 类型 | 约束 | 说明 |
|--------|------|------|------|
| id | INTEGER | PK, AUTOINCREMENT | 目标ID |
| user_id | INTEGER | NOT NULL, FK | 用户ID |
| title | VARCHAR(200) | NOT NULL | 目标标题 |
| description | TEXT | - | 目标描述 |
| category | VARCHAR(50) | CHECK | 类别 |
| status | VARCHAR(20) | DEFAULT 'active' | 状态 |
| priority | VARCHAR(10) | DEFAULT 'medium' | 优先级 |
| visibility | VARCHAR(20) | DEFAULT 'private' | 可见性 |
| deadline | DATE | - | 截止日期 |
| start_date | DATE | - | 开始日期 |
| completed_at | DATETIME | - | 完成时间 |
| progress_percentage | INTEGER | DEFAULT 0 | 进度百分比 |
| related_strengths | JSON | - | 相关优势 |
| success_criteria | TEXT | - | 成功标准 |
| obstacles | TEXT | - | 可能障碍 |
| support_needed | TEXT | - | 需要的支持 |
| progress_notes | TEXT | - | 进展笔记 |
| created_at | DATETIME | DEFAULT CURRENT_TIMESTAMP | 创建时间 |
| updated_at | DATETIME | DEFAULT CURRENT_TIMESTAMP | 更新时间 |

**目标类别 (category)**:
- `career` - 职业发展
- `relationship` - 人际关系
- `health` - 健康
- `learning` - 学习成长
- `finance` - 财务
- `personal` - 个人
- `other` - 其他

#### 4.2 goal_milestones - 目标里程碑表

| 字段名 | 类型 | 约束 | 说明 |
|--------|------|------|------|
| id | INTEGER | PK, AUTOINCREMENT | 里程碑ID |
| goal_id | INTEGER | NOT NULL, FK | 目标ID |
| title | VARCHAR(200) | NOT NULL | 标题 |
| description | TEXT | - | 描述 |
| status | VARCHAR(20) | DEFAULT 'pending' | 状态 |
| target_date | DATE | - | 目标日期 |
| completed_at | DATETIME | - | 完成时间 |
| order_index | INTEGER | DEFAULT 0 | 排序索引 |
| created_at | DATETIME | DEFAULT CURRENT_TIMESTAMP | 创建时间 |
| updated_at | DATETIME | DEFAULT CURRENT_TIMESTAMP | 更新时间 |

#### 4.3 goal_progress - 目标进展记录表

| 字段名 | 类型 | 约束 | 说明 |
|--------|------|------|------|
| id | INTEGER | PK, AUTOINCREMENT | 记录ID |
| goal_id | INTEGER | NOT NULL, FK | 目标ID |
| progress_type | VARCHAR(30) | DEFAULT 'check_in' | 进展类型 |
| content | TEXT | NOT NULL | 内容 |
| progress_value | INTEGER | - | 进展数值 |
| emotion_tag | VARCHAR(30) | - | 情绪标签 |
| related_conversation_id | INTEGER | FK | 相关对话ID |
| created_at | DATETIME | DEFAULT CURRENT_TIMESTAMP | 创建时间 |

---

### 5. 订阅与支付相关表

#### 5.1 subscriptions - 订阅表

| 字段名 | 类型 | 约束 | 说明 |
|--------|------|------|------|
| id | INTEGER | PK, AUTOINCREMENT | 订阅ID |
| user_id | INTEGER | NOT NULL, FK | 用户ID |
| plan_type | VARCHAR(20) | NOT NULL, CHECK | 计划类型 |
| billing_cycle | VARCHAR(20) | DEFAULT 'monthly' | 计费周期 |
| status | VARCHAR(20) | DEFAULT 'active' | 状态 |
| price | DECIMAL(10,2) | NOT NULL | 价格 |
| currency | VARCHAR(3) | DEFAULT 'CNY' | 货币 |
| start_date | DATE | NOT NULL | 开始日期 |
| end_date | DATE | - | 结束日期 |
| trial_end_date | DATE | - | 试用结束日期 |
| auto_renew | BOOLEAN | DEFAULT TRUE | 自动续费 |
| payment_provider | VARCHAR(50) | - | 支付提供商 |
| provider_subscription_id | VARCHAR(255) | - | 第三方订阅ID |
| cancellation_reason | TEXT | - | 取消原因 |
| cancelled_at | DATETIME | - | 取消时间 |
| created_at | DATETIME | DEFAULT CURRENT_TIMESTAMP | 创建时间 |
| updated_at | DATETIME | DEFAULT CURRENT_TIMESTAMP | 更新时间 |

**计划类型 (plan_type)**:
- `free` - 免费版
- `basic` - 基础版
- `premium` - 高级版
- `enterprise` - 企业版

#### 5.2 payments - 支付记录表

| 字段名 | 类型 | 约束 | 说明 |
|--------|------|------|------|
| id | INTEGER | PK, AUTOINCREMENT | 支付ID |
| user_id | INTEGER | NOT NULL, FK | 用户ID |
| subscription_id | INTEGER | FK | 订阅ID |
| payment_type | VARCHAR(20) | DEFAULT 'subscription' | 支付类型 |
| amount | DECIMAL(10,2) | NOT NULL | 金额 |
| currency | VARCHAR(3) | DEFAULT 'CNY' | 货币 |
| status | VARCHAR(20) | DEFAULT 'pending' | 状态 |
| payment_method | VARCHAR(50) | - | 支付方式 |
| payment_provider | VARCHAR(50) | - | 支付提供商 |
| provider_transaction_id | VARCHAR(255) | - | 第三方交易ID |
| description | TEXT | - | 描述 |
| metadata | JSON | - | 元数据 |
| paid_at | DATETIME | - | 支付时间 |
| created_at | DATETIME | DEFAULT CURRENT_TIMESTAMP | 创建时间 |

#### 5.3 usage_quotas - 使用配额表

| 字段名 | 类型 | 约束 | 说明 |
|--------|------|------|------|
| id | INTEGER | PK, AUTOINCREMENT | 配额ID |
| user_id | INTEGER | UNIQUE, NOT NULL, FK | 用户ID |
| plan_type | VARCHAR(20) | NOT NULL | 计划类型 |
| conversation_limit | INTEGER | DEFAULT 10 | 对话限制 |
| conversation_used | INTEGER | DEFAULT 0 | 已用对话数 |
| message_limit | INTEGER | DEFAULT 100 | 消息限制 |
| message_used | INTEGER | DEFAULT 0 | 已用消息数 |
| assessment_limit | INTEGER | DEFAULT 1 | 评估限制 |
| assessment_used | INTEGER | DEFAULT 0 | 已用评估数 |
| ai_call_limit | INTEGER | DEFAULT 100 | AI调用限制 |
| ai_call_used | INTEGER | DEFAULT 0 | 已用AI调用数 |
| quota_period | VARCHAR(20) | DEFAULT 'monthly' | 配额周期 |
| period_start | DATE | - | 周期开始 |
| period_end | DATE | - | 周期结束 |
| extra_quota | JSON | - | 额外配额 |
| created_at | DATETIME | DEFAULT CURRENT_TIMESTAMP | 创建时间 |
| updated_at | DATETIME | DEFAULT CURRENT_TIMESTAMP | 更新时间 |

---

### 6. 教练知识库相关表

#### 6.1 coach_knowledge - 教练知识库表

| 字段名 | 类型 | 约束 | 说明 |
|--------|------|------|------|
| id | INTEGER | PK, AUTOINCREMENT | 知识ID |
| category | VARCHAR(50) | NOT NULL, CHECK | 类别 |
| topic | VARCHAR(100) | NOT NULL | 主题 |
| subtopic | VARCHAR(100) | - | 子主题 |
| title | VARCHAR(200) | NOT NULL | 标题 |
| content | TEXT | NOT NULL | 内容 |
| content_format | VARCHAR(20) | DEFAULT 'text' | 内容格式 |
| tags | JSON | - | 标签 |
| source | VARCHAR(200) | - | 来源 |
| author | VARCHAR(100) | - | 作者 |
| difficulty_level | VARCHAR(10) | DEFAULT 'intermediate' | 难度级别 |
| related_knowledge_ids | JSON | - | 相关知识ID |
| usage_count | INTEGER | DEFAULT 0 | 使用次数 |
| rating_average | REAL | DEFAULT 0 | 平均评分 |
| rating_count | INTEGER | DEFAULT 0 | 评分次数 |
| is_active | BOOLEAN | DEFAULT TRUE | 是否激活 |
| valid_from | DATE | - | 有效期从 |
| valid_until | DATE | - | 有效期至 |
| created_at | DATETIME | DEFAULT CURRENT_TIMESTAMP | 创建时间 |
| updated_at | DATETIME | DEFAULT CURRENT_TIMESTAMP | 更新时间 |

**知识类别 (category)**:
- `strength_theory` - 优势理论
- `coaching_technique` - 教练技术
- `psychology` - 心理学
- `case_study` - 案例研究
- `tool` - 工具
- `faq` - 常见问题

#### 6.2 strength_definitions - 优势定义表

| 字段名 | 类型 | 约束 | 说明 |
|--------|------|------|------|
| id | INTEGER | PK, AUTOINCREMENT | 定义ID |
| strength_key | VARCHAR(50) | UNIQUE, NOT NULL | 优势代码 |
| name_zh | VARCHAR(100) | NOT NULL | 中文名称 |
| name_en | VARCHAR(100) | NOT NULL | 英文名称 |
| virtue_category | VARCHAR(50) | NOT NULL | 美德类别 |
| definition | TEXT | NOT NULL | 定义 |
| description | TEXT | - | 详细描述 |
| characteristics | JSON | - | 特征 |
| applications | JSON | - | 应用场景 |
| development_tips | TEXT | - | 发展建议 |
| overuse_risks | TEXT | - | 过度使用风险 |
| related_strengths | JSON | - | 相关优势 |
| famous_examples | JSON | - | 著名案例 |
| assessment_questions | JSON | - | 评估问题 |
| icon_url | TEXT | - | 图标URL |
| color_code | VARCHAR(7) | - | 颜色代码 |
| sort_order | INTEGER | - | 排序 |
| is_active | BOOLEAN | DEFAULT TRUE | 是否激活 |
| created_at | DATETIME | DEFAULT CURRENT_TIMESTAMP | 创建时间 |
| updated_at | DATETIME | DEFAULT CURRENT_TIMESTAMP | 更新时间 |

**美德类别 (virtue_category)**:
- `智慧` - 智慧与知识
- `勇气` - 勇气
- `仁爱` - 人道
- `正义` - 公正
- `节制` - 节制
- `超越` - 超越

#### 6.3 coach_prompts - 教练提示词模板表

| 字段名 | 类型 | 约束 | 说明 |
|--------|------|------|------|
| id | INTEGER | PK, AUTOINCREMENT | 模板ID |
| prompt_type | VARCHAR(50) | NOT NULL, CHECK | 提示词类型 |
| name | VARCHAR(100) | NOT NULL | 名称 |
| description | TEXT | - | 描述 |
| template | TEXT | NOT NULL | 模板内容 |
| variables | JSON | - | 模板变量 |
| context_conditions | JSON | - | 适用条件 |
| priority | INTEGER | DEFAULT 0 | 优先级 |
| is_default | BOOLEAN | DEFAULT FALSE | 是否默认 |
| model_config | JSON | - | AI模型配置 |
| usage_count | INTEGER | DEFAULT 0 | 使用次数 |
| success_rate | REAL | - | 成功率 |
| is_active | BOOLEAN | DEFAULT TRUE | 是否激活 |
| created_at | DATETIME | DEFAULT CURRENT_TIMESTAMP | 创建时间 |
| updated_at | DATETIME | DEFAULT CURRENT_TIMESTAMP | 更新时间 |

**提示词类型 (prompt_type)**:
- `system` - 系统提示词
- `greeting` - 问候语
- `strength_analysis` - 优势分析
- `goal_setting` - 目标设定
- `action_planning` - 行动计划
- `reflection` - 反思引导
- `encouragement` - 鼓励支持
- `crisis_support` - 危机支持

---

### 7. 系统管理与审计相关表

#### 7.1 system_configs - 系统配置表

| 字段名 | 类型 | 约束 | 说明 |
|--------|------|------|------|
| id | INTEGER | PK, AUTOINCREMENT | 配置ID |
| config_key | VARCHAR(100) | UNIQUE, NOT NULL | 配置键 |
| config_value | TEXT | NOT NULL | 配置值 |
| config_type | VARCHAR(20) | DEFAULT 'string' | 配置类型 |
| description | TEXT | - | 描述 |
| category | VARCHAR(50) | - | 类别 |
| is_editable | BOOLEAN | DEFAULT TRUE | 是否可编辑 |
| created_at | DATETIME | DEFAULT CURRENT_TIMESTAMP | 创建时间 |
| updated_at | DATETIME | DEFAULT CURRENT_TIMESTAMP | 更新时间 |

#### 7.2 audit_logs - 操作审计日志表

| 字段名 | 类型 | 约束 | 说明 |
|--------|------|------|------|
| id | INTEGER | PK, AUTOINCREMENT | 日志ID |
| user_id | INTEGER | FK | 用户ID |
| action | VARCHAR(50) | NOT NULL | 操作类型 |
| entity_type | VARCHAR(50) | NOT NULL | 实体类型 |
| entity_id | INTEGER | - | 实体ID |
| old_values | JSON | - | 旧值 |
| new_values | JSON | - | 新值 |
| ip_address | VARCHAR(45) | - | IP地址 |
| user_agent | TEXT | - | 用户代理 |
| session_id | VARCHAR(255) | - | 会话ID |
| metadata | JSON | - | 元数据 |
| created_at | DATETIME | DEFAULT CURRENT_TIMESTAMP | 创建时间 |

#### 7.3 app_logs - 应用日志表

| 字段名 | 类型 | 约束 | 说明 |
|--------|------|------|------|
| id | INTEGER | PK, AUTOINCREMENT | 日志ID |
| log_level | VARCHAR(10) | NOT NULL, CHECK | 日志级别 |
| source | VARCHAR(50) | NOT NULL | 日志来源 |
| message | TEXT | NOT NULL | 消息内容 |
| details | JSON | - | 详细信息 |
| user_id | INTEGER | FK | 用户ID |
| request_id | VARCHAR(100) | - | 请求ID |
| created_at | DATETIME | DEFAULT CURRENT_TIMESTAMP | 创建时间 |

**日志级别 (log_level)**: DEBUG, INFO, WARNING, ERROR, CRITICAL

---

### 8. 通知相关表

#### 8.1 notifications - 通知表

| 字段名 | 类型 | 约束 | 说明 |
|--------|------|------|------|
| id | INTEGER | PK, AUTOINCREMENT | 通知ID |
| user_id | INTEGER | NOT NULL, FK | 用户ID |
| notification_type | VARCHAR(30) | NOT NULL, CHECK | 通知类型 |
| title | VARCHAR(200) | NOT NULL | 标题 |
| content | TEXT | NOT NULL | 内容 |
| action_url | TEXT | - | 操作链接 |
| action_type | VARCHAR(50) | - | 操作类型 |
| related_entity_type | VARCHAR(50) | - | 相关实体类型 |
| related_entity_id | INTEGER | - | 相关实体ID |
| priority | VARCHAR(10) | DEFAULT 'normal' | 优先级 |
| is_read | BOOLEAN | DEFAULT FALSE | 是否已读 |
| read_at | DATETIME | - | 阅读时间 |
| is_sent | BOOLEAN | DEFAULT FALSE | 是否已发送 |
| sent_at | DATETIME | - | 发送时间 |
| send_channel | VARCHAR(20) | CHECK | 发送渠道 |
| expires_at | DATETIME | - | 过期时间 |
| created_at | DATETIME | DEFAULT CURRENT_TIMESTAMP | 创建时间 |

**通知类型 (notification_type)**:
- `system` - 系统通知
- `coach` - 教练消息
- `goal` - 目标提醒
- `assessment` - 评估通知
- `subscription` - 订阅通知
- `reminder` - 提醒

---

## 索引设计

### 用户相关索引

```sql
-- 用户表索引
CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_users_status ON users(status);
CREATE INDEX idx_users_subscription_type ON users(subscription_type);
CREATE INDEX idx_users_created_at ON users(created_at);

-- 用户画像表索引
CREATE INDEX idx_user_profiles_user_id ON user_profiles(user_id);

-- 用户令牌表索引
CREATE INDEX idx_user_tokens_user_id ON user_tokens(user_id);
CREATE INDEX idx_user_tokens_token_hash ON user_tokens(token_hash);
CREATE INDEX idx_user_tokens_expires_at ON user_tokens(expires_at);
```

### 对话相关索引

```sql
-- 对话表索引
CREATE INDEX idx_conversations_user_id ON conversations(user_id);
CREATE INDEX idx_conversations_status ON conversations(status);
CREATE INDEX idx_conversations_created_at ON conversations(created_at);

-- 消息表索引
CREATE INDEX idx_messages_conversation_id ON messages(conversation_id);
CREATE INDEX idx_messages_role ON messages(role);
CREATE INDEX idx_messages_created_at ON messages(created_at);
CREATE INDEX idx_messages_conversation_created ON messages(conversation_id, created_at);
```

### 评估相关索引

```sql
-- 评估表索引
CREATE INDEX idx_assessments_user_id ON assessments(user_id);
CREATE INDEX idx_assessments_type ON assessments(assessment_type);
CREATE INDEX idx_assessments_status ON assessments(status);
CREATE INDEX idx_assessments_completed_at ON assessments(completed_at);

-- 评估结果表索引
CREATE INDEX idx_assessment_results_assessment_id ON assessment_results(assessment_id);
CREATE INDEX idx_assessment_results_dimension ON assessment_results(dimension_name);
```

### 目标相关索引

```sql
-- 目标表索引
CREATE INDEX idx_goals_user_id ON goals(user_id);
CREATE INDEX idx_goals_status ON goals(status);
CREATE INDEX idx_goals_deadline ON goals(deadline);
CREATE INDEX idx_goals_category ON goals(category);

-- 目标里程碑表索引
CREATE INDEX idx_goal_milestones_goal_id ON goal_milestones(goal_id);

-- 目标进展表索引
CREATE INDEX idx_goal_progress_goal_id ON goal_progress(goal_id);
CREATE INDEX idx_goal_progress_created_at ON goal_progress(created_at);
```

### 订阅相关索引

```sql
-- 订阅表索引
CREATE INDEX idx_subscriptions_user_id ON subscriptions(user_id);
CREATE INDEX idx_subscriptions_status ON subscriptions(status);
CREATE INDEX idx_subscriptions_end_date ON subscriptions(end_date);

-- 支付表索引
CREATE INDEX idx_payments_user_id ON payments(user_id);
CREATE INDEX idx_payments_status ON payments(status);
CREATE INDEX idx_payments_provider_transaction_id ON payments(provider_transaction_id);
```

### 知识库相关索引

```sql
-- 知识库表索引
CREATE INDEX idx_coach_knowledge_category ON coach_knowledge(category);
CREATE INDEX idx_coach_knowledge_topic ON coach_knowledge(topic);
CREATE INDEX idx_coach_knowledge_is_active ON coach_knowledge(is_active);

-- 优势定义表索引
CREATE INDEX idx_strength_definitions_key ON strength_definitions(strength_key);
CREATE INDEX idx_strength_definitions_virtue ON strength_definitions(virtue_category);

-- 教练提示词表索引
CREATE INDEX idx_coach_prompts_type ON coach_prompts(prompt_type);
CREATE INDEX idx_coach_prompts_is_active ON coach_prompts(is_active);
```

### 审计日志相关索引

```sql
-- 审计日志表索引
CREATE INDEX idx_audit_logs_user_id ON audit_logs(user_id);
CREATE INDEX idx_audit_logs_action ON audit_logs(action);
CREATE INDEX idx_audit_logs_entity ON audit_logs(entity_type, entity_id);
CREATE INDEX idx_audit_logs_created_at ON audit_logs(created_at);

-- 应用日志表索引
CREATE INDEX idx_app_logs_level ON app_logs(log_level);
CREATE INDEX idx_app_logs_source ON app_logs(source);
CREATE INDEX idx_app_logs_created_at ON app_logs(created_at);

-- 通知表索引
CREATE INDEX idx_notifications_user_id ON notifications(user_id);
CREATE INDEX idx_notifications_is_read ON notifications(is_read);
CREATE INDEX idx_notifications_type ON notifications(notification_type);
CREATE INDEX idx_notifications_created_at ON notifications(created_at);
```

---

## 数据关系说明

### 核心关系图

```
┌─────────────────────────────────────────────────────────────────┐
│                        数据关系总览                               │
└─────────────────────────────────────────────────────────────────┘

用户中心关系:
┌─────────┐    1:1    ┌─────────────┐
│  users  │───────────│user_profiles│
└────┬────┘           └─────────────┘
     │
     │ 1:N
     ├──► conversations ──► messages
     │
     ├──► assessments ──► assessment_results
     │              │
     │              └──► assessment_responses
     │
     ├──► goals ──► goal_milestones
     │        │
     │        └──► goal_progress
     │
     ├──► subscriptions ──► payments
     │
     ├──► user_tokens
     │
     ├──► usage_quotas
     │
     ├──► notifications
     │
     └──► audit_logs

知识库关系:
┌──────────────────┐    ┌───────────────────┐    ┌──────────────┐
│strength_definitions│    │  coach_knowledge  │    │coach_prompts │
└──────────────────┘    └───────────────────┘    └──────────────┘
```

### 级联操作说明

| 父表 | 子表 | 删除操作 | 说明 |
|------|------|----------|------|
| users | user_profiles | CASCADE | 删除用户同时删除画像 |
| users | user_tokens | CASCADE | 删除用户同时删除令牌 |
| users | conversations | CASCADE | 删除用户同时删除对话 |
| users | assessments | CASCADE | 删除用户同时删除评估 |
| users | goals | CASCADE | 删除用户同时删除目标 |
| users | subscriptions | CASCADE | 删除用户同时删除订阅 |
| users | usage_quotas | CASCADE | 删除用户同时删除配额 |
| users | notifications | CASCADE | 删除用户同时删除通知 |
| users | audit_logs | SET NULL | 保留审计记录但清空用户ID |
| users | app_logs | SET NULL | 保留日志但清空用户ID |
| conversations | messages | CASCADE | 删除对话同时删除消息 |
| conversations | conversation_summaries | CASCADE | 删除对话同时删除摘要 |
| messages | messages (parent) | SET NULL | 父消息删除时清空引用 |
| assessments | assessment_results | CASCADE | 删除评估同时删除结果 |
| assessments | assessment_responses | CASCADE | 删除评估同时删除答题 |
| goals | goal_milestones | CASCADE | 删除目标同时删除里程碑 |
| goals | goal_progress | CASCADE | 删除目标同时删除进展 |
| subscriptions | payments | SET NULL | 删除订阅时保留支付记录 |

---

## SQL建表脚本

完整的SQLite建表脚本位于: `/mnt/okcomputer/output/backend/database/schema.sql`

### 使用说明

```bash
# 创建新数据库
sqlite3 ai_coach.db < schema.sql

# 或在现有数据库中执行
sqlite3 ai_coach.db
.read schema.sql
```

### 脚本包含内容

1. **表结构定义** - 所有22个数据表的完整定义
2. **约束设置** - 主键、外键、CHECK约束
3. **索引创建** - 50+个性能优化索引
4. **触发器** - 自动更新updated_at字段
5. **初始数据**:
   - 系统配置默认值
   - VIA 24种性格优势定义
   - 教练提示词模板

---

## 数据字典

### 枚举值定义

#### 用户状态 (users.status)
| 值 | 说明 |
|----|------|
| active | 正常 |
| inactive | 未激活 |
| suspended | 已暂停 |
| deleted | 已删除 |

#### 订阅类型 (users.subscription_type / subscriptions.plan_type)
| 值 | 说明 |
|----|------|
| free | 免费版 |
| basic | 基础版 |
| premium | 高级版 |
| enterprise | 企业版 |

#### 评估类型 (assessments.assessment_type)
| 值 | 说明 |
|----|------|
| via_strengths | VIA性格优势评估 |
| mbti | MBTI性格测试 |
| disc | DISC行为风格 |
| big_five | 大五人格 |
| custom | 自定义评估 |
| weekly_checkin | 周度检查 |
| goal_progress | 目标进展评估 |

#### 目标类别 (goals.category)
| 值 | 说明 |
|----|------|
| career | 职业发展 |
| relationship | 人际关系 |
| health | 健康 |
| learning | 学习成长 |
| finance | 财务 |
| personal | 个人 |
| other | 其他 |

#### 美德类别 (strength_definitions.virtue_category)
| 值 | 说明 |
|----|------|
| 智慧 | 智慧与知识 |
| 勇气 | 勇气 |
| 仁爱 | 人道 |
| 正义 | 公正 |
| 节制 | 节制 |
| 超越 | 超越 |

---

## 附录

### VIA 24种性格优势

| 编号 | 优势代码 | 中文名称 | 英文名称 | 美德类别 |
|------|----------|----------|----------|----------|
| 1 | creativity | 创造力 | Creativity | 智慧 |
| 2 | curiosity | 好奇心 | Curiosity | 智慧 |
| 3 | judgment | 判断力 | Judgment | 智慧 |
| 4 | love_of_learning | 热爱学习 | Love of Learning | 智慧 |
| 5 | perspective | 洞察力 | Perspective | 智慧 |
| 6 | bravery | 勇敢 | Bravery | 勇气 |
| 7 | perseverance | 毅力 | Perseverance | 勇气 |
| 8 | honesty | 诚实 | Honesty | 勇气 |
| 9 | zest | 热情 | Zest | 勇气 |
| 10 | love | 爱与被爱 | Love | 仁爱 |
| 11 | kindness | 善良 | Kindness | 仁爱 |
| 12 | social_intelligence | 社交智慧 | Social Intelligence | 仁爱 |
| 13 | teamwork | 团队合作 | Teamwork | 正义 |
| 14 | fairness | 公平 | Fairness | 正义 |
| 15 | leadership | 领导力 | Leadership | 正义 |
| 16 | forgiveness | 宽恕 | Forgiveness | 节制 |
| 17 | humility | 谦逊 | Humility | 节制 |
| 18 | prudence | 审慎 | Prudence | 节制 |
| 19 | self_regulation | 自我调节 | Self-Regulation | 节制 |
| 20 | appreciation_of_beauty | 审美 | Appreciation of Beauty | 超越 |
| 21 | gratitude | 感恩 | Gratitude | 超越 |
| 22 | hope | 希望 | Hope | 超越 |
| 23 | humor | 幽默 | Humor | 超越 |
| 24 | spirituality | 灵性 | Spirituality | 超越 |

---

## 版本历史

| 版本 | 日期 | 说明 |
|------|------|------|
| 1.0.0 | 2024 | 初始版本，包含MVP所需全部表结构 |

---

*文档结束*
