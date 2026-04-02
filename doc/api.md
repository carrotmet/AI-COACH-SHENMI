# 深觅 AI Coach - API接口文档

> 文档版本: v1.0.0  
> 最后更新: 2024-XX-XX  
> 技术栈: Python + FastAPI + SQLite + JavaScript + LazyLLM

---

## 目录

1. [接口概览](#1-接口概览)
2. [认证方式](#2-认证方式)
3. [错误码定义](#3-错误码定义)
4. [用户认证接口](#4-用户认证接口)
5. [用户管理接口](#5-用户管理接口)
6. [测评系统接口](#6-测评系统接口)
7. [对话系统接口](#7-对话系统接口)
8. [订阅管理接口](#8-订阅管理接口)

---

## 1. 接口概览

### 1.1 基础信息

| 项目 | 说明 |
|------|------|
| 基础URL | `http://localhost:8000/api/v1` (开发环境) |
| 协议 | HTTP/HTTPS |
| 数据格式 | JSON |
| 字符编码 | UTF-8 |

### 1.2 接口列表概览

| 接口分类 | 接口数量 | 说明 |
|----------|----------|------|
| 用户认证 | 4 | 注册、登录、登出、Token刷新 |
| 用户管理 | 5 | 用户信息、配置、历史记录 |
| 测评系统 | 6 | 测评创建、答题、结果分析 |
| 对话系统 | 4 | 对话创建、消息发送、历史查询 |
| 订阅管理 | 3 | 订阅查询、购买、取消 |

---

## 2. 认证方式

### 2.1 JWT Token认证

本系统使用 JWT (JSON Web Token) 进行身份认证。

**请求头格式:**
```
Authorization: Bearer <access_token>
```

### 2.2 Token类型

| Token类型 | 有效期 | 用途 |
|-----------|--------|------|
| Access Token | 15分钟 | 接口访问认证 |
| Refresh Token | 7天 | 刷新Access Token |

### 2.3 认证流程

```
┌─────────────┐     登录请求      ┌─────────────┐
│   客户端     │ ───────────────> │   服务端     │
│  (Client)   │                  │  (Server)   │
└─────────────┘                  └─────────────┘
       ^                               │
       │    返回 Access + Refresh      │
       │    Token                      │
       └───────────────────────────────┘
       │
       │    携带 Access Token
       │    访问受保护接口
       └───────────────────────────────>
```

---

## 3. 错误码定义

### 3.1 HTTP状态码

| 状态码 | 说明 | 场景 |
|--------|------|------|
| 200 | OK | 请求成功 |
| 201 | Created | 资源创建成功 |
| 400 | Bad Request | 请求参数错误 |
| 401 | Unauthorized | 未认证或Token过期 |
| 403 | Forbidden | 无权限访问 |
| 404 | Not Found | 资源不存在 |
| 422 | Validation Error | 参数校验失败 |
| 429 | Too Many Requests | 请求过于频繁 |
| 500 | Internal Server Error | 服务器内部错误 |

### 3.2 业务错误码

| 错误码 | 错误信息 | 说明 |
|--------|----------|------|
| 1001 | 用户已存在 | 注册时用户名/邮箱已存在 |
| 1002 | 用户不存在 | 登录时用户不存在 |
| 1003 | 密码错误 | 登录密码不正确 |
| 1004 | Token无效 | Token格式错误或已过期 |
| 1005 | Token已过期 | Access Token过期 |
| 1006 | 刷新Token无效 | Refresh Token无效或过期 |
| 2001 | 测评不存在 | 请求的测评ID不存在 |
| 2002 | 测评已完成 | 测评已经提交完成 |
| 2003 | 答案无效 | 提交的答案格式错误 |
| 3001 | 对话不存在 | 对话会话ID不存在 |
| 3002 | 消息发送失败 | AI服务调用失败 |
| 4001 | 订阅已过期 | 用户订阅已到期 |
| 4002 | 订阅次数不足 | 免费次数已用完 |

### 3.3 错误响应格式

```json
{
  "code": 1001,
  "message": "用户已存在",
  "detail": "该邮箱已被注册",
  "timestamp": "2024-01-15T10:30:00Z"
}
```

---

## 4. 用户认证接口

### 4.1 用户注册

**接口信息**

| 项目 | 内容 |
|------|------|
| URL | `/auth/register` |
| 方法 | POST |
| 认证 | 否 |

**请求参数**

| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| email | string | 是 | 用户邮箱 |
| password | string | 是 | 密码(6-20位) |
| nickname | string | 否 | 用户昵称 |

**请求示例**
```json
{
  "email": "user@example.com",
  "password": "password123",
  "nickname": "小明"
}
```

**响应格式**

| 字段 | 类型 | 说明 |
|------|------|------|
| user_id | string | 用户唯一标识 |
| email | string | 用户邮箱 |
| nickname | string | 用户昵称 |
| created_at | string | 注册时间 |
| access_token | string | 访问令牌 |
| refresh_token | string | 刷新令牌 |

**成功响应示例**
```json
{
  "code": 200,
  "data": {
    "user_id": "usr_123456789",
    "email": "user@example.com",
    "nickname": "小明",
    "created_at": "2024-01-15T10:30:00Z",
    "access_token": "eyJhbGciOiJIUzI1NiIs...",
    "refresh_token": "eyJhbGciOiJIUzI1NiIs..."
  }
}
```

**错误示例**
```json
{
  "code": 1001,
  "message": "用户已存在",
  "detail": "该邮箱已被注册"
}
```

---

### 4.2 用户登录

**接口信息**

| 项目 | 内容 |
|------|------|
| URL | `/auth/login` |
| 方法 | POST |
| 认证 | 否 |

**请求参数**

| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| email | string | 是 | 用户邮箱 |
| password | string | 是 | 密码 |

**请求示例**
```json
{
  "email": "user@example.com",
  "password": "password123"
}
```

**响应格式**

| 字段 | 类型 | 说明 |
|------|------|------|
| user_id | string | 用户唯一标识 |
| email | string | 用户邮箱 |
| nickname | string | 用户昵称 |
| access_token | string | 访问令牌 |
| refresh_token | string | 刷新令牌 |
| expires_in | int | Token有效期(秒) |

**成功响应示例**
```json
{
  "code": 200,
  "data": {
    "user_id": "usr_123456789",
    "email": "user@example.com",
    "nickname": "小明",
    "access_token": "eyJhbGciOiJIUzI1NiIs...",
    "refresh_token": "eyJhbGciOiJIUzI1NiIs...",
    "expires_in": 900
  }
}
```

**错误示例**
```json
{
  "code": 1002,
  "message": "用户不存在",
  "detail": "该邮箱未注册"
}
```

---

### 4.3 用户登出

**接口信息**

| 项目 | 内容 |
|------|------|
| URL | `/auth/logout` |
| 方法 | POST |
| 认证 | 是 |

**请求参数**

无

**响应格式**

| 字段 | 类型 | 说明 |
|------|------|------|
| message | string | 操作结果 |

**成功响应示例**
```json
{
  "code": 200,
  "data": {
    "message": "登出成功"
  }
}
```

---

### 4.4 刷新Token

**接口信息**

| 项目 | 内容 |
|------|------|
| URL | `/auth/refresh` |
| 方法 | POST |
| 认证 | 否 |

**请求参数**

| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| refresh_token | string | 是 | 刷新令牌 |

**请求示例**
```json
{
  "refresh_token": "eyJhbGciOiJIUzI1NiIs..."
}
```

**响应格式**

| 字段 | 类型 | 说明 |
|------|------|------|
| access_token | string | 新的访问令牌 |
| refresh_token | string | 新的刷新令牌 |
| expires_in | int | Token有效期(秒) |

**成功响应示例**
```json
{
  "code": 200,
  "data": {
    "access_token": "eyJhbGciOiJIUzI1NiIs...",
    "refresh_token": "eyJhbGciOiJIUzI1NiIs...",
    "expires_in": 900
  }
}
```

**错误示例**
```json
{
  "code": 1006,
  "message": "刷新Token无效",
  "detail": "Refresh Token已过期或无效"
}
```

---

## 5. 用户管理接口

### 5.1 获取用户信息

**接口信息**

| 项目 | 内容 |
|------|------|
| URL | `/users/me` |
| 方法 | GET |
| 认证 | 是 |

**请求参数**

无

**响应格式**

| 字段 | 类型 | 说明 |
|------|------|------|
| user_id | string | 用户唯一标识 |
| email | string | 用户邮箱 |
| nickname | string | 用户昵称 |
| avatar | string | 头像URL |
| created_at | string | 注册时间 |
| subscription | object | 订阅信息 |
| usage_stats | object | 使用统计 |

**成功响应示例**
```json
{
  "code": 200,
  "data": {
    "user_id": "usr_123456789",
    "email": "user@example.com",
    "nickname": "小明",
    "avatar": "https://example.com/avatar.jpg",
    "created_at": "2024-01-15T10:30:00Z",
    "subscription": {
      "type": "free",
      "expires_at": null,
      "remaining_assessments": 3
    },
    "usage_stats": {
      "total_assessments": 5,
      "total_conversations": 12,
      "last_active": "2024-01-20T15:30:00Z"
    }
  }
}
```

---

### 5.2 更新用户信息

**接口信息**

| 项目 | 内容 |
|------|------|
| URL | `/users/me` |
| 方法 | PUT |
| 认证 | 是 |

**请求参数**

| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| nickname | string | 否 | 用户昵称 |
| avatar | string | 否 | 头像URL |

**请求示例**
```json
{
  "nickname": "新昵称",
  "avatar": "https://example.com/new_avatar.jpg"
}
```

**响应格式**

| 字段 | 类型 | 说明 |
|------|------|------|
| user_id | string | 用户唯一标识 |
| nickname | string | 更新后的昵称 |
| avatar | string | 更新后的头像 |
| updated_at | string | 更新时间 |

**成功响应示例**
```json
{
  "code": 200,
  "data": {
    "user_id": "usr_123456789",
    "nickname": "新昵称",
    "avatar": "https://example.com/new_avatar.jpg",
    "updated_at": "2024-01-20T16:00:00Z"
  }
}
```

---

### 5.3 修改密码

**接口信息**

| 项目 | 内容 |
|------|------|
| URL | `/users/me/password` |
| 方法 | PUT |
| 认证 | 是 |

**请求参数**

| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| old_password | string | 是 | 旧密码 |
| new_password | string | 是 | 新密码(6-20位) |

**请求示例**
```json
{
  "old_password": "oldpass123",
  "new_password": "newpass456"
}
```

**响应格式**

| 字段 | 类型 | 说明 |
|------|------|------|
| message | string | 操作结果 |

**成功响应示例**
```json
{
  "code": 200,
  "data": {
    "message": "密码修改成功"
  }
}
```

**错误示例**
```json
{
  "code": 1003,
  "message": "密码错误",
  "detail": "旧密码不正确"
}
```

---

### 5.4 获取用户测评历史

**接口信息**

| 项目 | 内容 |
|------|------|
| URL | `/users/me/assessments` |
| 方法 | GET |
| 认证 | 是 |

**请求参数 (Query)**

| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| page | int | 否 | 页码，默认1 |
| limit | int | 否 | 每页数量，默认10 |

**响应格式**

| 字段 | 类型 | 说明 |
|------|------|------|
| items | array | 测评记录列表 |
| total | int | 总记录数 |
| page | int | 当前页码 |
| limit | int | 每页数量 |

**成功响应示例**
```json
{
  "code": 200,
  "data": {
    "items": [
      {
        "assessment_id": "asm_123456",
        "type": "strength",
        "status": "completed",
        "score": 85,
        "created_at": "2024-01-18T10:00:00Z",
        "completed_at": "2024-01-18T10:30:00Z"
      }
    ],
    "total": 5,
    "page": 1,
    "limit": 10
  }
}
```

---

### 5.5 获取用户对话历史

**接口信息**

| 项目 | 内容 |
|------|------|
| URL | `/users/me/conversations` |
| 方法 | GET |
| 认证 | 是 |

**请求参数 (Query)**

| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| page | int | 否 | 页码，默认1 |
| limit | int | 否 | 每页数量，默认10 |

**响应格式**

| 字段 | 类型 | 说明 |
|------|------|------|
| items | array | 对话记录列表 |
| total | int | 总记录数 |
| page | int | 当前页码 |
| limit | int | 每页数量 |

**成功响应示例**
```json
{
  "code": 200,
  "data": {
    "items": [
      {
        "conversation_id": "conv_123456",
        "title": "优势探索对话",
        "message_count": 15,
        "created_at": "2024-01-19T14:00:00Z",
        "updated_at": "2024-01-19T15:00:00Z"
      }
    ],
    "total": 12,
    "page": 1,
    "limit": 10
  }
}
```

---

## 6. 测评系统接口

### 6.1 创建测评

**接口信息**

| 项目 | 内容 |
|------|------|
| URL | `/assessments` |
| 方法 | POST |
| 认证 | 是 |

**请求参数**

| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| type | string | 是 | 测评类型: strength(优势测评) |
| language | string | 否 | 语言: zh(中文)/en(英文)，默认zh |

**请求示例**
```json
{
  "type": "strength",
  "language": "zh"
}
```

**响应格式**

| 字段 | 类型 | 说明 |
|------|------|------|
| assessment_id | string | 测评唯一标识 |
| type | string | 测评类型 |
| status | string | 状态: pending(进行中) |
| total_questions | int | 总题目数 |
| current_question | int | 当前题目序号 |
| created_at | string | 创建时间 |

**成功响应示例**
```json
{
  "code": 200,
  "data": {
    "assessment_id": "asm_123456",
    "type": "strength",
    "status": "pending",
    "total_questions": 34,
    "current_question": 1,
    "created_at": "2024-01-20T10:00:00Z"
  }
}
```

**错误示例**
```json
{
  "code": 4002,
  "message": "订阅次数不足",
  "detail": "免费测评次数已用完，请升级订阅"
}
```

---

### 6.2 获取测评题目

**接口信息**

| 项目 | 内容 |
|------|------|
| URL | `/assessments/{assessment_id}/questions` |
| 方法 | GET |
| 认证 | 是 |

**路径参数**

| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| assessment_id | string | 是 | 测评ID |

**响应格式**

| 字段 | 类型 | 说明 |
|------|------|------|
| assessment_id | string | 测评ID |
| current_question | int | 当前题目序号 |
| total_questions | int | 总题目数 |
| question | object | 题目内容 |

**成功响应示例**
```json
{
  "code": 200,
  "data": {
    "assessment_id": "asm_123456",
    "current_question": 5,
    "total_questions": 34,
    "question": {
      "id": 5,
      "text": "当面对困难时，你通常会...",
      "options": [
        {"id": "A", "text": "寻找创新的解决方案"},
        {"id": "B", "text": "寻求他人的帮助和建议"},
        {"id": "C", "text": "依靠过去的经验"},
        {"id": "D", "text": "仔细分析问题再行动"}
      ]
    }
  }
}
```

**错误示例**
```json
{
  "code": 2001,
  "message": "测评不存在",
  "detail": "测评ID无效或已删除"
}
```

---

### 6.3 提交答案

**接口信息**

| 项目 | 内容 |
|------|------|
| URL | `/assessments/{assessment_id}/answers` |
| 方法 | POST |
| 认证 | 是 |

**路径参数**

| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| assessment_id | string | 是 | 测评ID |

**请求参数**

| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| question_id | int | 是 | 题目ID |
| answer | string | 是 | 选项ID (A/B/C/D) |

**请求示例**
```json
{
  "question_id": 5,
  "answer": "A"
}
```

**响应格式**

| 字段 | 类型 | 说明 |
|------|------|------|
| assessment_id | string | 测评ID |
| current_question | int | 下一题序号 |
| total_questions | int | 总题目数 |
| is_completed | bool | 是否完成 |
| next_question | object/null | 下一题内容(未完成时) |

**成功响应示例 - 未完成**
```json
{
  "code": 200,
  "data": {
    "assessment_id": "asm_123456",
    "current_question": 6,
    "total_questions": 34,
    "is_completed": false,
    "next_question": {
      "id": 6,
      "text": "在团队合作中，你更倾向于...",
      "options": [...]
    }
  }
}
```

**成功响应示例 - 已完成**
```json
{
  "code": 200,
  "data": {
    "assessment_id": "asm_123456",
    "current_question": 34,
    "total_questions": 34,
    "is_completed": true,
    "next_question": null,
    "result_url": "/assessments/asm_123456/result"
  }
}
```

---

### 6.4 获取测评结果

**接口信息**

| 项目 | 内容 |
|------|------|
| URL | `/assessments/{assessment_id}/result` |
| 方法 | GET |
| 认证 | 是 |

**路径参数**

| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| assessment_id | string | 是 | 测评ID |

**响应格式**

| 字段 | 类型 | 说明 |
|------|------|------|
| assessment_id | string | 测评ID |
| status | string | 状态: completed |
| completed_at | string | 完成时间 |
| top_strengths | array | 前5项优势 |
| detailed_analysis | object | 详细分析 |
| recommendations | array | 发展建议 |

**成功响应示例**
```json
{
  "code": 200,
  "data": {
    "assessment_id": "asm_123456",
    "status": "completed",
    "completed_at": "2024-01-20T10:45:00Z",
    "top_strengths": [
      {
        "rank": 1,
        "name": "战略思维",
        "score": 92,
        "description": "善于从全局角度思考问题，制定长远计划"
      },
      {
        "rank": 2,
        "name": "学习力",
        "score": 88,
        "description": "对新知识充满好奇，学习能力强"
      }
    ],
    "detailed_analysis": {
      "executing": {"score": 75, "strengths": [...]},
      "influencing": {"score": 82, "strengths": [...]},
      "relationship": {"score": 70, "strengths": [...]},
      "thinking": {"score": 90, "strengths": [...]}
    },
    "recommendations": [
      "利用战略思维优势，在项目中承担规划角色",
      "持续学习新技能，保持竞争优势"
    ]
  }
}
```

---

### 6.5 获取测评进度

**接口信息**

| 项目 | 内容 |
|------|------|
| URL | `/assessments/{assessment_id}/progress` |
| 方法 | GET |
| 认证 | 是 |

**路径参数**

| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| assessment_id | string | 是 | 测评ID |

**响应格式**

| 字段 | 类型 | 说明 |
|------|------|------|
| assessment_id | string | 测评ID |
| status | string | 状态 |
| progress_percent | int | 完成百分比 |
| answered_count | int | 已答题目数 |
| total_count | int | 总题目数 |
| last_answered_at | string | 最后答题时间 |

**成功响应示例**
```json
{
  "code": 200,
  "data": {
    "assessment_id": "asm_123456",
    "status": "pending",
    "progress_percent": 44,
    "answered_count": 15,
    "total_count": 34,
    "last_answered_at": "2024-01-20T10:30:00Z"
  }
}
```

---

### 6.6 删除测评

**接口信息**

| 项目 | 内容 |
|------|------|
| URL | `/assessments/{assessment_id}` |
| 方法 | DELETE |
| 认证 | 是 |

**路径参数**

| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| assessment_id | string | 是 | 测评ID |

**响应格式**

| 字段 | 类型 | 说明 |
|------|------|------|
| message | string | 操作结果 |

**成功响应示例**
```json
{
  "code": 200,
  "data": {
    "message": "测评已删除"
  }
}
```

---

## 7. 对话系统接口

### 7.1 创建对话

**接口信息**

| 项目 | 内容 |
|------|------|
| URL | `/conversations` |
| 方法 | POST |
| 认证 | 是 |

**请求参数**

| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| title | string | 否 | 对话标题 |
| context | object | 否 | 对话上下文(如测评结果) |

**请求示例**
```json
{
  "title": "优势探索对话",
  "context": {
    "assessment_id": "asm_123456",
    "top_strengths": ["战略思维", "学习力"]
  }
}
```

**响应格式**

| 字段 | 类型 | 说明 |
|------|------|------|
| conversation_id | string | 对话唯一标识 |
| title | string | 对话标题 |
| created_at | string | 创建时间 |

**成功响应示例**
```json
{
  "code": 200,
  "data": {
    "conversation_id": "conv_123456",
    "title": "优势探索对话",
    "created_at": "2024-01-20T11:00:00Z"
  }
}
```

---

### 7.2 发送消息

**接口信息**

| 项目 | 内容 |
|------|------|
| URL | `/conversations/{conversation_id}/messages` |
| 方法 | POST |
| 认证 | 是 |

**路径参数**

| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| conversation_id | string | 是 | 对话ID |

**请求参数**

| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| content | string | 是 | 消息内容 |
| type | string | 否 | 消息类型: text(默认) |

**请求示例**
```json
{
  "content": "我想了解更多关于战略思维的优势如何应用",
  "type": "text"
}
```

**响应格式**

| 字段 | 类型 | 说明 |
|------|------|------|
| message_id | string | 消息唯一标识 |
| conversation_id | string | 对话ID |
| user_message | object | 用户发送的消息 |
| ai_message | object | AI回复的消息 |
| timestamp | string | 时间戳 |

**成功响应示例**
```json
{
  "code": 200,
  "data": {
    "message_id": "msg_123456",
    "conversation_id": "conv_123456",
    "user_message": {
      "id": "msg_user_001",
      "role": "user",
      "content": "我想了解更多关于战略思维的优势如何应用",
      "timestamp": "2024-01-20T11:05:00Z"
    },
    "ai_message": {
      "id": "msg_ai_001",
      "role": "assistant",
      "content": "战略思维是一种非常宝贵的优势...",
      "timestamp": "2024-01-20T11:05:05Z"
    },
    "timestamp": "2024-01-20T11:05:05Z"
  }
}
```

**错误示例**
```json
{
  "code": 3002,
  "message": "消息发送失败",
  "detail": "AI服务暂时不可用，请稍后重试"
}
```

---

### 7.3 获取对话历史

**接口信息**

| 项目 | 内容 |
|------|------|
| URL | `/conversations/{conversation_id}/messages` |
| 方法 | GET |
| 认证 | 是 |

**路径参数**

| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| conversation_id | string | 是 | 对话ID |

**请求参数 (Query)**

| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| page | int | 否 | 页码，默认1 |
| limit | int | 否 | 每页数量，默认20 |

**响应格式**

| 字段 | 类型 | 说明 |
|------|------|------|
| conversation_id | string | 对话ID |
| messages | array | 消息列表 |
| total | int | 总消息数 |
| page | int | 当前页码 |
| limit | int | 每页数量 |

**成功响应示例**
```json
{
  "code": 200,
  "data": {
    "conversation_id": "conv_123456",
    "messages": [
      {
        "id": "msg_001",
        "role": "user",
        "content": "你好",
        "timestamp": "2024-01-20T11:00:00Z"
      },
      {
        "id": "msg_002",
        "role": "assistant",
        "content": "你好！我是你的AI优势教练...",
        "timestamp": "2024-01-20T11:00:05Z"
      }
    ],
    "total": 15,
    "page": 1,
    "limit": 20
  }
}
```

---

### 7.4 删除对话

**接口信息**

| 项目 | 内容 |
|------|------|
| URL | `/conversations/{conversation_id}` |
| 方法 | DELETE |
| 认证 | 是 |

**路径参数**

| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| conversation_id | string | 是 | 对话ID |

**响应格式**

| 字段 | 类型 | 说明 |
|------|------|------|
| message | string | 操作结果 |

**成功响应示例**
```json
{
  "code": 200,
  "data": {
    "message": "对话已删除"
  }
}
```

---

## 8. 订阅管理接口

### 8.1 获取订阅信息

**接口信息**

| 项目 | 内容 |
|------|------|
| URL | `/subscription` |
| 方法 | GET |
| 认证 | 是 |

**请求参数**

无

**响应格式**

| 字段 | 类型 | 说明 |
|------|------|------|
| type | string | 订阅类型: free/premium |
| start_date | string/null | 订阅开始时间 |
| expires_at | string/null | 订阅到期时间 |
| features | object | 功能权限 |
| usage | object | 使用情况 |

**成功响应示例 - 免费用户**
```json
{
  "code": 200,
  "data": {
    "type": "free",
    "start_date": null,
    "expires_at": null,
    "features": {
      "max_assessments": 3,
      "max_conversations": 10,
      "ai_coach": true,
      "advanced_analysis": false
    },
    "usage": {
      "assessments_used": 2,
      "assessments_remaining": 1,
      "conversations_used": 5,
      "conversations_remaining": 5
    }
  }
}
```

**成功响应示例 - 付费用户**
```json
{
  "code": 200,
  "data": {
    "type": "premium",
    "start_date": "2024-01-01T00:00:00Z",
    "expires_at": "2025-01-01T00:00:00Z",
    "features": {
      "max_assessments": -1,
      "max_conversations": -1,
      "ai_coach": true,
      "advanced_analysis": true
    },
    "usage": {
      "assessments_used": 10,
      "assessments_remaining": -1,
      "conversations_used": 50,
      "conversations_remaining": -1
    }
  }
}
```

---

### 8.2 获取订阅计划

**接口信息**

| 项目 | 内容 |
|------|------|
| URL | `/subscription/plans` |
| 方法 | GET |
| 认证 | 否 |

**请求参数**

无

**响应格式**

| 字段 | 类型 | 说明 |
|------|------|------|
| plans | array | 订阅计划列表 |

**成功响应示例**
```json
{
  "code": 200,
  "data": {
    "plans": [
      {
        "id": "free",
        "name": "免费版",
        "price": 0,
        "currency": "CNY",
        "period": "永久",
        "features": [
          "3次免费测评",
          "10次对话",
          "基础AI教练"
        ]
      },
      {
        "id": "premium_monthly",
        "name": "高级版(月付)",
        "price": 29.9,
        "currency": "CNY",
        "period": "月",
        "features": [
          "无限次测评",
          "无限次对话",
          "高级AI教练",
          "深度分析报告"
        ]
      },
      {
        "id": "premium_yearly",
        "name": "高级版(年付)",
        "price": 299,
        "currency": "CNY",
        "period": "年",
        "discount": "17%",
        "features": [
          "无限次测评",
          "无限次对话",
          "高级AI教练",
          "深度分析报告"
        ]
      }
    ]
  }
}
```

---

### 8.3 创建订阅订单

**接口信息**

| 项目 | 内容 |
|------|------|
| URL | `/subscription/orders` |
| 方法 | POST |
| 认证 | 是 |

**请求参数**

| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| plan_id | string | 是 | 计划ID |
| payment_method | string | 是 | 支付方式: wechat/alipay |

**请求示例**
```json
{
  "plan_id": "premium_monthly",
  "payment_method": "wechat"
}
```

**响应格式**

| 字段 | 类型 | 说明 |
|------|------|------|
| order_id | string | 订单唯一标识 |
| plan_id | string | 计划ID |
| amount | number | 金额 |
| currency | string | 货币 |
| payment_url | string | 支付跳转URL |
| expires_at | string | 订单过期时间 |

**成功响应示例**
```json
{
  "code": 200,
  "data": {
    "order_id": "ord_123456",
    "plan_id": "premium_monthly",
    "amount": 29.9,
    "currency": "CNY",
    "payment_url": "https://pay.example.com/...",
    "expires_at": "2024-01-20T12:00:00Z"
  }
}
```

---

## 附录

### A. 接口版本历史

| 版本 | 日期 | 变更内容 |
|------|------|----------|
| v1.0.0 | 2024-XX-XX | 初始版本，MVP功能接口 |

### B. 测试环境

- 基础URL: `http://localhost:8000/api/v1`
- 测试账号: `test@example.com` / `test123`

### C. 相关文档

- [设计文档](./design.md)
- [数据库文档](./database.md)
- [更新日志](./changelog.md)
