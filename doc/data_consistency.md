# 前后端数据一致性说明

## 1. API请求/响应格式

### 统一响应格式
```json
{
    "code": 200,
    "message": "success",
    "data": {},
    "timestamp": 1234567890
}
```

### 认证相关

#### 注册请求
**前端发送:**
```json
{
    "email": "user@example.com",
    "password": "password123",
    "username": "用户名" (可选)
}
```

**后端接收:** `RegisterRequest` 模型
- email: EmailStr (必填)
- password: str (必填, 最小6位)
- username: str (可选)

#### 登录请求
**前端发送:**
```json
{
    "email": "user@example.com",
    "password": "password123"
}
```

**后端接收:** `LoginRequest` 模型
- email: EmailStr (必填)
- password: str (必填)

#### 登录响应
**后端返回:**
```json
{
    "code": 200,
    "message": "登录成功",
    "data": {
        "access_token": "xxx",
        "refresh_token": "xxx",
        "token_type": "bearer",
        "expires_in": 900,
        "user": {
            "id": 1,
            "email": "user@example.com",
            "username": "用户名"
        }
    }
}
```

### 测评相关

#### 创建测评
**前端发送:** POST /api/v1/assessments
```json
{
    "assessment_type": "via_strengths"
}
```

**后端接收:**
- assessment_type: str (必填, 如 "via_strengths")

#### 提交答案
**前端发送:** POST /api/v1/assessments/{id}/answers
```json
{
    "answers": [
        {"question_id": 1, "score": 5},
        {"question_id": 2, "score": 4}
    ]
}
```

**后端接收:**
- answers: List[Dict] (必填)
  - question_id: int
  - score: int (1-5)

#### 获取结果
**后端返回:**
```json
{
    "code": 200,
    "message": "success",
    "data": {
        "assessment_id": 1,
        "assessment_type": "via_strengths",
        "status": "completed",
        "scores": {
            "curiosity": 85,
            "creativity": 78
        },
        "top_strengths": ["curiosity", "creativity", "kindness"],
        "interpretation": "解读文本..."
    }
}
```

### 对话相关

#### 发送消息
**前端发送:** POST /api/v1/conversations/{id}/messages
```json
{
    "content": "消息内容"
}
```

**后端接收:**
- content: str (必填)

**后端返回:**
```json
{
    "code": 200,
    "message": "success",
    "data": {
        "message_id": 123,
        "conversation_id": 1,
        "role": "assistant",
        "content": "AI回复内容",
        "emotion_tag": "positive",
        "timestamp": "2024-01-01T12:00:00"
    }
}
```

## 2. 字段命名对照表

| 前端字段 | 后端字段 | 说明 |
|---------|---------|------|
| email | email | 用户邮箱 |
| password | password | 密码 |
| username | username | 用户名 |
| assessmentType | assessment_type | 测评类型 |
| answers | answers | 答案数组 |
| questionId | question_id | 题目ID |
| score | score | 分数 |
| content | content | 消息内容 |
| conversationId | conversation_id | 对话ID |
| accessToken | access_token | 访问令牌 |
| refreshToken | refresh_token | 刷新令牌 |

## 3. 注意事项

1. ** snake_case vs camelCase **
   - 后端使用 snake_case (Python惯例)
   - 前端可以使用 camelCase，但发送请求时需转换为 snake_case
   - 或在后端配置 Pydantic 模型支持别名

2. **日期时间格式**
   - 后端返回 ISO 8601 格式: "2024-01-01T12:00:00"
   - 前端需要正确解析

3. **枚举值**
   - 使用字符串枚举，如 "via_strengths", "active"
   - 避免使用数字代码

4. **空值处理**
   - 使用 null 而非 undefined
   - 后端使用 Optional 类型
