-- =====================================================
-- 深寻觅 AI Coach - 数据库架构脚本 (SQLite)
-- 版本: 1.0.0
-- 创建日期: 2024
-- =====================================================

-- 启用外键约束
PRAGMA foreign_keys = ON;

-- =====================================================
-- 1. 用户管理相关表
-- =====================================================

-- 用户基础信息表
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username VARCHAR(50) UNIQUE NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    phone VARCHAR(20) UNIQUE,
    avatar_url TEXT,
    status VARCHAR(20) DEFAULT 'active' CHECK (status IN ('active', 'inactive', 'suspended', 'deleted')),
    subscription_type VARCHAR(20) DEFAULT 'free' CHECK (subscription_type IN ('free', 'basic', 'premium', 'enterprise')),
    email_verified BOOLEAN DEFAULT FALSE,
    phone_verified BOOLEAN DEFAULT FALSE,
    last_login_at DATETIME,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    deleted_at DATETIME  -- 软删除标记
);

-- 用户画像表
CREATE TABLE IF NOT EXISTS user_profiles (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER UNIQUE NOT NULL,
    nickname VARCHAR(50),
    gender VARCHAR(10) CHECK (gender IN ('male', 'female', 'other', 'prefer_not_to_say')),
    birth_date DATE,
    occupation VARCHAR(100),
    company VARCHAR(100),
    industry VARCHAR(50),
    location VARCHAR(100),
    bio TEXT,
    goals TEXT,  -- 用户目标描述
    interests TEXT,  -- 兴趣爱好，逗号分隔
    strengths_profile JSON,  -- 优势档案 (JSON格式存储34种优势评分)
    personality_type VARCHAR(10),  -- MBTI等性格类型
    preferences JSON,  -- 用户偏好设置
    coaching_style_preference VARCHAR(20),  -- 教练风格偏好
    notification_settings JSON DEFAULT '{"email": true, "push": true, "sms": false}',
    privacy_settings JSON DEFAULT '{"profile_visible": false, "share_anonymous_data": true}',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

-- 用户认证令牌表 (支持多设备登录)
CREATE TABLE IF NOT EXISTS user_tokens (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    token_type VARCHAR(20) NOT NULL CHECK (token_type IN ('access', 'refresh', 'api')),
    token_hash VARCHAR(255) NOT NULL,
    device_info JSON,  -- 设备信息
    ip_address VARCHAR(45),
    expires_at DATETIME NOT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    last_used_at DATETIME,
    revoked BOOLEAN DEFAULT FALSE,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

-- =====================================================
-- 2. 对话系统相关表
-- =====================================================

-- 对话会话表
CREATE TABLE IF NOT EXISTS conversations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    title VARCHAR(200) DEFAULT '新对话',
    status VARCHAR(20) DEFAULT 'active' CHECK (status IN ('active', 'archived', 'deleted')),
    coach_type VARCHAR(30) DEFAULT 'strength' CHECK (coach_type IN ('strength', 'career', 'relationship', 'wellness', 'general')),
    context JSON,  -- 对话上下文信息
    metadata JSON,  -- 额外元数据
    message_count INTEGER DEFAULT 0,
    started_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    ended_at DATETIME,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

-- 消息记录表
CREATE TABLE IF NOT EXISTS messages (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    conversation_id INTEGER NOT NULL,
    role VARCHAR(20) NOT NULL CHECK (role IN ('user', 'assistant', 'system', 'coach')),
    content TEXT NOT NULL,
    content_type VARCHAR(20) DEFAULT 'text' CHECK (content_type IN ('text', 'image', 'audio', 'file', 'structured')),
    emotion_tag VARCHAR(30),  -- 情绪标签
    sentiment_score REAL CHECK (sentiment_score BETWEEN -1 AND 1),  -- 情感分析分数
    model_info JSON,  -- AI模型信息
    tokens_used INTEGER,  -- 使用的token数
    response_time_ms INTEGER,  -- 响应时间(毫秒)
    is_edited BOOLEAN DEFAULT FALSE,
    edited_at DATETIME,
    parent_message_id INTEGER,  -- 回复的消息ID
    attachments JSON,  -- 附件信息
    metadata JSON,  -- 额外元数据
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (conversation_id) REFERENCES conversations(id) ON DELETE CASCADE,
    FOREIGN KEY (parent_message_id) REFERENCES messages(id) ON DELETE SET NULL
);

-- 对话摘要表 (用于快速回顾)
CREATE TABLE IF NOT EXISTS conversation_summaries (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    conversation_id INTEGER UNIQUE NOT NULL,
    summary TEXT,  -- 对话摘要
    key_points JSON,  -- 关键要点
    action_items JSON,  -- 行动项
    topics JSON,  -- 讨论主题
    sentiment_overview VARCHAR(50),
    generated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (conversation_id) REFERENCES conversations(id) ON DELETE CASCADE
);

-- =====================================================
-- 3. 评估系统相关表
-- =====================================================

-- 评估记录表
CREATE TABLE IF NOT EXISTS assessments (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    assessment_type VARCHAR(30) NOT NULL CHECK (assessment_type IN ('via_strengths', 'mbti', 'disc', 'big_five', 'custom', 'weekly_checkin', 'goal_progress')),
    title VARCHAR(200),
    description TEXT,
    status VARCHAR(20) DEFAULT 'pending' CHECK (status IN ('pending', 'in_progress', 'completed', 'expired', 'cancelled')),
    version VARCHAR(10) DEFAULT '1.0',
    score_summary JSON,  -- 评分汇总
    interpretation TEXT,  -- 结果解读
    recommendations JSON,  -- 建议
    started_at DATETIME,
    completed_at DATETIME,
    valid_until DATETIME,  -- 结果有效期
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

-- 评估结果详情表
CREATE TABLE IF NOT EXISTS assessment_results (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    assessment_id INTEGER NOT NULL,
    dimension_name VARCHAR(100) NOT NULL,  -- 维度名称
    dimension_code VARCHAR(50),  -- 维度代码
    category VARCHAR(50),  -- 所属类别
    score REAL NOT NULL,  -- 原始分数
    normalized_score REAL,  -- 标准化分数(0-100)
    percentile INTEGER CHECK (percentile BETWEEN 0 AND 100),  -- 百分位
    rank INTEGER,  -- 排名
    interpretation TEXT,  -- 维度解读
    strengths_description TEXT,  -- 优势描述
    development_tips TEXT,  -- 发展建议
    related_strengths JSON,  -- 相关优势
    metadata JSON,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (assessment_id) REFERENCES assessments(id) ON DELETE CASCADE
);

-- 评估答题记录表
CREATE TABLE IF NOT EXISTS assessment_responses (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    assessment_id INTEGER NOT NULL,
    question_id VARCHAR(50) NOT NULL,
    question_text TEXT,
    response_value TEXT NOT NULL,  -- 回答值
    response_score REAL,  -- 评分
    response_time_ms INTEGER,  -- 答题用时
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (assessment_id) REFERENCES assessments(id) ON DELETE CASCADE
);

-- =====================================================
-- 4. 目标管理相关表
-- =====================================================

-- 用户目标表
CREATE TABLE IF NOT EXISTS goals (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    title VARCHAR(200) NOT NULL,
    description TEXT,
    category VARCHAR(50) CHECK (category IN ('career', 'relationship', 'health', 'learning', 'finance', 'personal', 'other')),
    status VARCHAR(20) DEFAULT 'active' CHECK (status IN ('draft', 'active', 'paused', 'completed', 'abandoned')),
    priority VARCHAR(10) DEFAULT 'medium' CHECK (priority IN ('low', 'medium', 'high', 'urgent')),
    visibility VARCHAR(20) DEFAULT 'private' CHECK (visibility IN ('private', 'coach_only', 'public')),
    deadline DATE,
    start_date DATE,
    completed_at DATETIME,
    progress_percentage INTEGER DEFAULT 0 CHECK (progress_percentage BETWEEN 0 AND 100),
    related_strengths JSON,  -- 相关的优势
    success_criteria TEXT,  -- 成功标准
    obstacles TEXT,  -- 可能的障碍
    support_needed TEXT,  -- 需要的支持
    progress_notes TEXT,  -- 进展笔记
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

-- 目标里程碑表
CREATE TABLE IF NOT EXISTS goal_milestones (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    goal_id INTEGER NOT NULL,
    title VARCHAR(200) NOT NULL,
    description TEXT,
    status VARCHAR(20) DEFAULT 'pending' CHECK (status IN ('pending', 'in_progress', 'completed', 'skipped')),
    target_date DATE,
    completed_at DATETIME,
    order_index INTEGER DEFAULT 0,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (goal_id) REFERENCES goals(id) ON DELETE CASCADE
);

-- 目标进展记录表
CREATE TABLE IF NOT EXISTS goal_progress (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    goal_id INTEGER NOT NULL,
    progress_type VARCHAR(30) DEFAULT 'check_in' CHECK (progress_type IN ('check_in', 'milestone', 'reflection', 'obstacle', 'breakthrough')),
    content TEXT NOT NULL,
    progress_value INTEGER,  -- 进展数值
    emotion_tag VARCHAR(30),
    related_conversation_id INTEGER,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (goal_id) REFERENCES goals(id) ON DELETE CASCADE,
    FOREIGN KEY (related_conversation_id) REFERENCES conversations(id) ON DELETE SET NULL
);

-- =====================================================
-- 5. 订阅与支付相关表
-- =====================================================

-- 订阅表
CREATE TABLE IF NOT EXISTS subscriptions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    plan_type VARCHAR(20) NOT NULL CHECK (plan_type IN ('free', 'basic', 'premium', 'enterprise')),
    billing_cycle VARCHAR(20) DEFAULT 'monthly' CHECK (billing_cycle IN ('monthly', 'quarterly', 'yearly')),
    status VARCHAR(20) DEFAULT 'active' CHECK (status IN ('active', 'cancelled', 'expired', 'suspended', 'trial')),
    price DECIMAL(10, 2) NOT NULL,
    currency VARCHAR(3) DEFAULT 'CNY',
    start_date DATE NOT NULL,
    end_date DATE,
    trial_end_date DATE,
    auto_renew BOOLEAN DEFAULT TRUE,
    payment_provider VARCHAR(50),  -- 支付提供商
    provider_subscription_id VARCHAR(255),  -- 第三方支付订阅ID
    cancellation_reason TEXT,
    cancelled_at DATETIME,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

-- 支付记录表
CREATE TABLE IF NOT EXISTS payments (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    subscription_id INTEGER,
    payment_type VARCHAR(20) DEFAULT 'subscription' CHECK (payment_type IN ('subscription', 'one_time', 'refund', 'credit')),
    amount DECIMAL(10, 2) NOT NULL,
    currency VARCHAR(3) DEFAULT 'CNY',
    status VARCHAR(20) DEFAULT 'pending' CHECK (status IN ('pending', 'completed', 'failed', 'refunded', 'cancelled')),
    payment_method VARCHAR(50),  -- 支付方式
    payment_provider VARCHAR(50),
    provider_transaction_id VARCHAR(255),
    description TEXT,
    metadata JSON,
    paid_at DATETIME,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (subscription_id) REFERENCES subscriptions(id) ON DELETE SET NULL
);

-- 使用配额表
CREATE TABLE IF NOT EXISTS usage_quotas (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER UNIQUE NOT NULL,
    plan_type VARCHAR(20) NOT NULL,
    -- 对话配额
    conversation_limit INTEGER DEFAULT 10,
    conversation_used INTEGER DEFAULT 0,
    -- 消息配额
    message_limit INTEGER DEFAULT 100,
    message_used INTEGER DEFAULT 0,
    -- 评估配额
    assessment_limit INTEGER DEFAULT 1,
    assessment_used INTEGER DEFAULT 0,
    -- AI调用配额
    ai_call_limit INTEGER DEFAULT 100,
    ai_call_used INTEGER DEFAULT 0,
    -- 配额周期
    quota_period VARCHAR(20) DEFAULT 'monthly' CHECK (quota_period IN ('daily', 'weekly', 'monthly')),
    period_start DATE,
    period_end DATE,
    extra_quota JSON,  -- 额外配额
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

-- =====================================================
-- 6. 教练知识库相关表
-- =====================================================

-- 教练知识库表
CREATE TABLE IF NOT EXISTS coach_knowledge (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    category VARCHAR(50) NOT NULL CHECK (category IN ('strength_theory', 'coaching_technique', 'psychology', 'case_study', 'tool', 'faq')),
    topic VARCHAR(100) NOT NULL,
    subtopic VARCHAR(100),
    title VARCHAR(200) NOT NULL,
    content TEXT NOT NULL,
    content_format VARCHAR(20) DEFAULT 'text' CHECK (content_format IN ('text', 'markdown', 'structured', 'template')),
    tags JSON,  -- 标签
    source VARCHAR(200),  -- 来源
    author VARCHAR(100),
    difficulty_level VARCHAR(10) DEFAULT 'intermediate' CHECK (difficulty_level IN ('beginner', 'intermediate', 'advanced')),
    related_knowledge_ids JSON,  -- 相关知识ID
    usage_count INTEGER DEFAULT 0,  -- 使用次数
    rating_average REAL DEFAULT 0,  -- 平均评分
    rating_count INTEGER DEFAULT 0,  -- 评分次数
    is_active BOOLEAN DEFAULT TRUE,
    valid_from DATE,
    valid_until DATE,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- 优势定义表 (VIA 24种性格优势)
CREATE TABLE IF NOT EXISTS strength_definitions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    strength_key VARCHAR(50) UNIQUE NOT NULL,  -- 优势代码
    name_zh VARCHAR(100) NOT NULL,  -- 中文名称
    name_en VARCHAR(100) NOT NULL,  -- 英文名称
    virtue_category VARCHAR(50) NOT NULL,  -- 美德类别 (智慧、勇气、仁爱、正义、节制、超越)
    definition TEXT NOT NULL,  -- 定义
    description TEXT,  -- 详细描述
    characteristics JSON,  -- 特征
    applications JSON,  -- 应用场景
    development_tips TEXT,  -- 发展建议
    overuse_risks TEXT,  -- 过度使用风险
    related_strengths JSON,  -- 相关优势
    famous_examples JSON,  -- 著名案例
    assessment_questions JSON,  -- 评估问题
    icon_url TEXT,
    color_code VARCHAR(7),
    sort_order INTEGER,
    is_active BOOLEAN DEFAULT TRUE,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- 教练提示词模板表
CREATE TABLE IF NOT EXISTS coach_prompts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    prompt_type VARCHAR(50) NOT NULL CHECK (prompt_type IN ('system', 'greeting', 'strength_analysis', 'goal_setting', 'action_planning', 'reflection', 'encouragement', 'crisis_support')),
    name VARCHAR(100) NOT NULL,
    description TEXT,
    template TEXT NOT NULL,  -- 提示词模板
    variables JSON,  -- 模板变量
    context_conditions JSON,  -- 适用条件
    priority INTEGER DEFAULT 0,
    is_default BOOLEAN DEFAULT FALSE,
    model_config JSON,  -- AI模型配置
    usage_count INTEGER DEFAULT 0,
    success_rate REAL,  -- 成功率
    is_active BOOLEAN DEFAULT TRUE,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- =====================================================
-- 7. 系统管理与审计相关表
-- =====================================================

-- 系统配置表
CREATE TABLE IF NOT EXISTS system_configs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    config_key VARCHAR(100) UNIQUE NOT NULL,
    config_value TEXT NOT NULL,
    config_type VARCHAR(20) DEFAULT 'string' CHECK (config_type IN ('string', 'number', 'boolean', 'json')),
    description TEXT,
    category VARCHAR(50),
    is_editable BOOLEAN DEFAULT TRUE,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- 操作审计日志表
CREATE TABLE IF NOT EXISTS audit_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    action VARCHAR(50) NOT NULL,  -- 操作类型
    entity_type VARCHAR(50) NOT NULL,  -- 实体类型
    entity_id INTEGER,  -- 实体ID
    old_values JSON,  -- 旧值
    new_values JSON,  -- 新值
    ip_address VARCHAR(45),
    user_agent TEXT,
    session_id VARCHAR(255),
    metadata JSON,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE SET NULL
);

-- 应用日志表
CREATE TABLE IF NOT EXISTS app_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    log_level VARCHAR(10) NOT NULL CHECK (log_level IN ('DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL')),
    source VARCHAR(50) NOT NULL,  -- 日志来源
    message TEXT NOT NULL,
    details JSON,
    user_id INTEGER,
    request_id VARCHAR(100),
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE SET NULL
);

-- =====================================================
-- 8. 通知与消息相关表
-- =====================================================

-- 通知表
CREATE TABLE IF NOT EXISTS notifications (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    notification_type VARCHAR(30) NOT NULL CHECK (notification_type IN ('system', 'coach', 'goal', 'assessment', 'subscription', 'reminder')),
    title VARCHAR(200) NOT NULL,
    content TEXT NOT NULL,
    action_url TEXT,  -- 操作链接
    action_type VARCHAR(50),  -- 操作类型
    related_entity_type VARCHAR(50),  -- 相关实体类型
    related_entity_id INTEGER,  -- 相关实体ID
    priority VARCHAR(10) DEFAULT 'normal' CHECK (priority IN ('low', 'normal', 'high', 'urgent')),
    is_read BOOLEAN DEFAULT FALSE,
    read_at DATETIME,
    is_sent BOOLEAN DEFAULT FALSE,
    sent_at DATETIME,
    send_channel VARCHAR(20) CHECK (send_channel IN ('in_app', 'email', 'push', 'sms')),
    expires_at DATETIME,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

-- =====================================================
-- 创建索引
-- =====================================================

-- 用户表索引
CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
CREATE INDEX IF NOT EXISTS idx_users_status ON users(status);
CREATE INDEX IF NOT EXISTS idx_users_subscription_type ON users(subscription_type);
CREATE INDEX IF NOT EXISTS idx_users_created_at ON users(created_at);

-- 用户画像表索引
CREATE INDEX IF NOT EXISTS idx_user_profiles_user_id ON user_profiles(user_id);

-- 用户令牌表索引
CREATE INDEX IF NOT EXISTS idx_user_tokens_user_id ON user_tokens(user_id);
CREATE INDEX IF NOT EXISTS idx_user_tokens_token_hash ON user_tokens(token_hash);
CREATE INDEX IF NOT EXISTS idx_user_tokens_expires_at ON user_tokens(expires_at);

-- 对话表索引
CREATE INDEX IF NOT EXISTS idx_conversations_user_id ON conversations(user_id);
CREATE INDEX IF NOT EXISTS idx_conversations_status ON conversations(status);
CREATE INDEX IF NOT EXISTS idx_conversations_created_at ON conversations(created_at);

-- 消息表索引
CREATE INDEX IF NOT EXISTS idx_messages_conversation_id ON messages(conversation_id);
CREATE INDEX IF NOT EXISTS idx_messages_role ON messages(role);
CREATE INDEX IF NOT EXISTS idx_messages_created_at ON messages(created_at);
CREATE INDEX IF NOT EXISTS idx_messages_conversation_created ON messages(conversation_id, created_at);

-- 评估表索引
CREATE INDEX IF NOT EXISTS idx_assessments_user_id ON assessments(user_id);
CREATE INDEX IF NOT EXISTS idx_assessments_type ON assessments(assessment_type);
CREATE INDEX IF NOT EXISTS idx_assessments_status ON assessments(status);
CREATE INDEX IF NOT EXISTS idx_assessments_completed_at ON assessments(completed_at);

-- 评估结果表索引
CREATE INDEX IF NOT EXISTS idx_assessment_results_assessment_id ON assessment_results(assessment_id);
CREATE INDEX IF NOT EXISTS idx_assessment_results_dimension ON assessment_results(dimension_name);

-- 目标表索引
CREATE INDEX IF NOT EXISTS idx_goals_user_id ON goals(user_id);
CREATE INDEX IF NOT EXISTS idx_goals_status ON goals(status);
CREATE INDEX IF NOT EXISTS idx_goals_deadline ON goals(deadline);
CREATE INDEX IF NOT EXISTS idx_goals_category ON goals(category);

-- 目标里程碑表索引
CREATE INDEX IF NOT EXISTS idx_goal_milestones_goal_id ON goal_milestones(goal_id);

-- 目标进展表索引
CREATE INDEX IF NOT EXISTS idx_goal_progress_goal_id ON goal_progress(goal_id);
CREATE INDEX IF NOT EXISTS idx_goal_progress_created_at ON goal_progress(created_at);

-- 订阅表索引
CREATE INDEX IF NOT EXISTS idx_subscriptions_user_id ON subscriptions(user_id);
CREATE INDEX IF NOT EXISTS idx_subscriptions_status ON subscriptions(status);
CREATE INDEX IF NOT EXISTS idx_subscriptions_end_date ON subscriptions(end_date);

-- 支付表索引
CREATE INDEX IF NOT EXISTS idx_payments_user_id ON payments(user_id);
CREATE INDEX IF NOT EXISTS idx_payments_status ON payments(status);
CREATE INDEX IF NOT EXISTS idx_payments_provider_transaction_id ON payments(provider_transaction_id);

-- 使用配额表索引
CREATE INDEX IF NOT EXISTS idx_usage_quotas_user_id ON usage_quotas(user_id);

-- 知识库表索引
CREATE INDEX IF NOT EXISTS idx_coach_knowledge_category ON coach_knowledge(category);
CREATE INDEX IF NOT EXISTS idx_coach_knowledge_topic ON coach_knowledge(topic);
CREATE INDEX IF NOT EXISTS idx_coach_knowledge_is_active ON coach_knowledge(is_active);

-- 优势定义表索引
CREATE INDEX IF NOT EXISTS idx_strength_definitions_key ON strength_definitions(strength_key);
CREATE INDEX IF NOT EXISTS idx_strength_definitions_virtue ON strength_definitions(virtue_category);

-- 教练提示词表索引
CREATE INDEX IF NOT EXISTS idx_coach_prompts_type ON coach_prompts(prompt_type);
CREATE INDEX IF NOT EXISTS idx_coach_prompts_is_active ON coach_prompts(is_active);

-- 审计日志表索引
CREATE INDEX IF NOT EXISTS idx_audit_logs_user_id ON audit_logs(user_id);
CREATE INDEX IF NOT EXISTS idx_audit_logs_action ON audit_logs(action);
CREATE INDEX IF NOT EXISTS idx_audit_logs_entity ON audit_logs(entity_type, entity_id);
CREATE INDEX IF NOT EXISTS idx_audit_logs_created_at ON audit_logs(created_at);

-- 应用日志表索引
CREATE INDEX IF NOT EXISTS idx_app_logs_level ON app_logs(log_level);
CREATE INDEX IF NOT EXISTS idx_app_logs_source ON app_logs(source);
CREATE INDEX IF NOT EXISTS idx_app_logs_created_at ON app_logs(created_at);

-- 通知表索引
CREATE INDEX IF NOT EXISTS idx_notifications_user_id ON notifications(user_id);
CREATE INDEX IF NOT EXISTS idx_notifications_is_read ON notifications(is_read);
CREATE INDEX IF NOT EXISTS idx_notifications_type ON notifications(notification_type);
CREATE INDEX IF NOT EXISTS idx_notifications_created_at ON notifications(created_at);

-- =====================================================
-- 创建触发器 (自动更新 updated_at)
-- =====================================================

CREATE TRIGGER IF NOT EXISTS trg_users_updated_at 
AFTER UPDATE ON users
BEGIN
    UPDATE users SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.id;
END;

CREATE TRIGGER IF NOT EXISTS trg_user_profiles_updated_at 
AFTER UPDATE ON user_profiles
BEGIN
    UPDATE user_profiles SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.id;
END;

CREATE TRIGGER IF NOT EXISTS trg_conversations_updated_at 
AFTER UPDATE ON conversations
BEGIN
    UPDATE conversations SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.id;
END;

CREATE TRIGGER IF NOT EXISTS trg_assessments_updated_at 
AFTER UPDATE ON assessments
BEGIN
    UPDATE assessments SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.id;
END;

CREATE TRIGGER IF NOT EXISTS trg_goals_updated_at 
AFTER UPDATE ON goals
BEGIN
    UPDATE goals SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.id;
END;

CREATE TRIGGER IF NOT EXISTS trg_goal_milestones_updated_at 
AFTER UPDATE ON goal_milestones
BEGIN
    UPDATE goal_milestones SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.id;
END;

CREATE TRIGGER IF NOT EXISTS trg_subscriptions_updated_at 
AFTER UPDATE ON subscriptions
BEGIN
    UPDATE subscriptions SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.id;
END;

CREATE TRIGGER IF NOT EXISTS trg_usage_quotas_updated_at 
AFTER UPDATE ON usage_quotas
BEGIN
    UPDATE usage_quotas SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.id;
END;

CREATE TRIGGER IF NOT EXISTS trg_coach_knowledge_updated_at 
AFTER UPDATE ON coach_knowledge
BEGIN
    UPDATE coach_knowledge SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.id;
END;

CREATE TRIGGER IF NOT EXISTS trg_strength_definitions_updated_at 
AFTER UPDATE ON strength_definitions
BEGIN
    UPDATE strength_definitions SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.id;
END;

CREATE TRIGGER IF NOT EXISTS trg_coach_prompts_updated_at 
AFTER UPDATE ON coach_prompts
BEGIN
    UPDATE coach_prompts SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.id;
END;

CREATE TRIGGER IF NOT EXISTS trg_system_configs_updated_at 
AFTER UPDATE ON system_configs
BEGIN
    UPDATE system_configs SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.id;
END;

-- =====================================================
-- 插入初始数据
-- =====================================================

-- 系统配置初始值
INSERT OR IGNORE INTO system_configs (config_key, config_value, config_type, description, category) VALUES
('app_name', '深寻觅 AI Coach', 'string', '应用名称', 'general'),
('app_version', '1.0.0', 'string', '应用版本', 'general'),
('max_conversation_length', '100', 'number', '单对话最大消息数', 'limits'),
('max_message_length', '4000', 'number', '单消息最大字符数', 'limits'),
('default_quota_conversations', '10', 'number', '默认对话配额', 'quota'),
('default_quota_messages', '100', 'number', '默认消息配额', 'quota'),
('default_quota_assessments', '1', 'number', '默认评估配额', 'quota'),
('session_timeout_hours', '24', 'number', '会话超时时间(小时)', 'security'),
('password_min_length', '8', 'number', '密码最小长度', 'security'),
('enable_email_verification', 'true', 'boolean', '启用邮箱验证', 'security');

-- VIA 24种性格优势初始数据
INSERT OR IGNORE INTO strength_definitions (strength_key, name_zh, name_en, virtue_category, definition, description, sort_order, color_code) VALUES
('creativity', '创造力', 'Creativity', '智慧', '能够想出新颖且有用的方法来做事情', '创造力是指能够产生新颖且有价值的想法、解决方案或作品的能力。具有创造力的人善于从不同角度思考问题，能够将看似无关的概念联系起来。', 1, '#9C27B0'),
('curiosity', '好奇心', 'Curiosity', '智慧', '对持续体验和新奇事物的兴趣', '好奇心是对世界保持开放和探索的态度，渴望学习新事物，体验新经历。好奇心强的人喜欢提问，对未知充满兴趣。', 2, '#673AB7'),
('judgment', '判断力', 'Judgment', '智慧', '能够从多角度思考，公平地审视证据', '判断力是指能够客观、理性地分析问题，权衡各种证据和观点，做出明智决策的能力。', 3, '#3F51B5'),
('love_of_learning', '热爱学习', 'Love of Learning', '智慧', '掌握新技能、增加新知识的热情', '热爱学习是指对新知识和技能有强烈的渴望，享受学习过程本身，而不仅仅是为了达到某个目标。', 4, '#2196F3'),
('perspective', '洞察力', 'Perspective', '智慧', '能够为他人提供明智的建议', '洞察力是指能够从更广阔的视角看待问题，理解事物的本质和意义，并能为他人提供有价值的建议。', 5, '#03A9F4'),
('bravery', '勇敢', 'Bravery', '勇气', '面对威胁、挑战、困难或痛苦时不退缩', '勇敢是指在面对恐惧、困难或危险时，仍然能够坚持正确的事情，不逃避挑战。', 6, '#00BCD4'),
('perseverance', '毅力', 'Perseverance', '勇气', '善始善终，在挫折中坚持不懈', '毅力是指在面对困难和挫折时能够坚持到底，不轻易放弃，直到完成目标。', 7, '#009688'),
('honesty', '诚实', 'Honesty', '勇气', '说实话，以真诚的方式呈现自己', '诚实是指言行一致，真实表达自己的想法和感受，不欺骗他人也不自欺欺人。', 8, '#4CAF50'),
('zest', '热情', 'Zest', '勇气', '对生活充满活力和热情', '热情是指对生活充满活力和激情，以积极的态度面对每一天，全身心地投入所做的事情。', 9, '#8BC34A'),
('love', '爱与被爱', 'Love', '仁爱', '重视与他人的亲密关系', '爱与被爱是指能够建立和维持亲密、温暖的人际关系，既能够付出爱，也能够接受爱。', 10, '#CDDC39'),
('kindness', '善良', 'Kindness', '仁爱', '乐于助人，关怀他人', '善良是指对他人的需求和感受敏感，愿意主动帮助需要帮助的人，表现出同情和关怀。', 11, '#FFEB3B'),
('social_intelligence', '社交智慧', 'Social Intelligence', '仁爱', '了解自己和他人动机和感受', '社交智慧是指能够理解自己和他人的情绪、动机和行为，善于处理人际关系。', 12, '#FFC107'),
('teamwork', '团队合作', 'Teamwork', '正义', '作为团队成员表现良好，忠诚于群体', '团队合作是指能够与他人协作，为共同目标努力，尊重团队成员，履行自己的责任。', 13, '#FF9800'),
('fairness', '公平', 'Fairness', '正义', '基于正义和公平的原则对待所有人', '公平是指能够公正地对待所有人，不偏袒任何一方，根据事实和原则做出判断。', 14, '#FF5722'),
('leadership', '领导力', 'Leadership', '正义', '组织团队活动并确保完成', '领导力是指能够激励和引导他人，组织团队实现共同目标，同时关心团队成员的成长。', 15, '#795548'),
('forgiveness', '宽恕', 'Forgiveness', '节制', '宽恕做错事的人，接受他人的不足', '宽恕是指能够原谅他人的过错，不记恨，给别人改正错误的机会，释放自己的负面情绪。', 16, '#9E9E9E'),
('humility', '谦逊', 'Humility', '节制', '不过度关注自己的成就', '谦逊是指能够客观看待自己的优点和缺点，不过度自夸，愿意向他人学习。', 17, '#607D8B'),
('prudence', '审慎', 'Prudence', '节制', '谨慎地做出选择，避免不当行为', '审慎是指能够深思熟虑，考虑长远后果，避免冲动行事，做出明智的选择。', 18, '#E91E63'),
('self_regulation', '自我调节', 'Self-Regulation', '节制', '调节自己的感受和行为', '自我调节是指能够控制自己的情绪、冲动和行为，坚持完成计划，抵制诱惑。', 19, '#F44336'),
('appreciation_of_beauty', '审美', 'Appreciation of Beauty', '超越', '欣赏各个领域的美和卓越', '审美是指能够发现和欣赏自然、艺术、科学等领域的美和卓越，被美好的事物所感动。', 20, '#9C27B0'),
('gratitude', '感恩', 'Gratitude', '超越', '感谢发生的好事，表达感谢', '感恩是指能够意识到并感谢生活中的美好事物，向帮助过自己的人表达谢意。', 21, '#673AB7'),
('hope', '希望', 'Hope', '超越', '期待未来最好的结果并努力实现', '希望是指对未来保持乐观的态度，相信事情会向好的方向发展，并为此付出努力。', 22, '#3F51B5'),
('humor', '幽默', 'Humor', '超越', '喜欢笑，为他人带来微笑', '幽默是指能够发现生活中的乐趣，用轻松愉快的方式看待问题，给他人带来快乐。', 23, '#2196F3'),
('spirituality', '灵性', 'Spirituality', '超越', '对更高目标和生命意义有信念', '灵性是指对生命意义、更高目标或超越性价值有追求和信念，能够从中获得力量和指引。', 24, '#03A9F4');

-- 教练提示词模板初始数据
INSERT OR IGNORE INTO coach_prompts (prompt_type, name, description, template, is_default, priority) VALUES
('system', '优势教练系统提示词', 'AI优势教练的核心系统提示词', '你是一位专业的优势教练，基于积极心理学和VIA性格优势理论。你的任务是帮助用户发现和发挥自己的优势，设定并实现个人目标。

核心原则：
1. 关注优势而非弱点
2. 使用GROW模型进行教练对话
3. 提出开放性问题，引导用户自我探索
4. 提供具体、可操作的建议
5. 保持同理心和支持性态度

用户优势档案：{{strengths_profile}}
当前对话目标：{{conversation_goal}}', TRUE, 100),

('greeting', '首次问候', '与新用户的首次对话问候', '你好！我是你的AI优势教练，很高兴认识你！🌟

我在这里帮助你：
• 发现和了解你的独特优势
• 设定并实现你的个人目标
• 在你成长的道路上提供支持和指导

为了更好地帮助你，我建议你先完成一次优势评估。这将帮助我们了解你的核心优势所在。

今天有什么我可以帮助你的吗？', TRUE, 90),

('strength_analysis', '优势分析', '分析用户的优势表现', '基于你的优势档案，我注意到你在【{{top_strength}}】方面表现突出。

这种优势在以下场景特别有价值：
{{applications}}

建议你可以：
{{suggestions}}

你想深入了解如何在日常生活中更好地运用这个优势吗？', TRUE, 80),

('goal_setting', '目标设定', '帮助用户设定SMART目标', '让我们用SMART原则来设定你的目标：

**具体 (Specific)**：你想要实现什么？
**可衡量 (Measurable)**：如何知道你已经达成了？
**可达成 (Achievable)**：这个目标现实吗？
**相关 (Relevant)**：为什么这个目标对你重要？
**有时限 (Time-bound)**：什么时候完成？

请告诉我你想实现的目标，我会帮你把它变得更清晰、更可行。', TRUE, 80),

('reflection', '反思引导', '引导用户进行深度反思', '让我们花点时间反思一下：

1. 回顾：最近发生了什么重要的事？
2. 感受：这件事让你有什么感受？
3. 洞察：你从这个经历中学到了什么？
4. 行动：基于这些洞察，你接下来想做什么？

慢慢来，我在这里倾听。', TRUE, 70),

('encouragement', '鼓励支持', '在用户遇到困难时给予鼓励', '我理解你现在可能感到{{emotion}}。这种感受是完全正常的。

请记住：
• 每个挑战都是成长的机会
• 你已经展现出了{{observed_strength}}的优势
• 我相信你有能力度过这个难关

让我们一起看看可以如何一步步地应对这个情况。你想从哪里开始？', TRUE, 70);

-- =====================================================
-- 数据库架构创建完成
-- =====================================================
