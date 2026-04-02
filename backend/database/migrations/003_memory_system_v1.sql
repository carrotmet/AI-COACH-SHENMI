-- ============================================================
-- 记忆系统v1 数据库迁移脚本
-- 创建时间: 2026-03-16
-- ============================================================

-- 1. 记忆来源映射表（Mem0记忆ID与对话关联）
CREATE TABLE IF NOT EXISTS memory_sources (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    memory_id VARCHAR(255) NOT NULL,          -- Mem0 返回的记忆ID
    conversation_id INTEGER NOT NULL,         -- 关联对话ID
    message_id INTEGER,                       -- 关联消息ID（可选）
    extraction_confidence FLOAT,              -- 提取置信度
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (conversation_id) REFERENCES conversations(id) ON DELETE CASCADE
);

-- 索引优化
CREATE INDEX IF NOT EXISTS idx_memory_sources_memory_id ON memory_sources(memory_id);
CREATE INDEX IF NOT EXISTS idx_memory_sources_conversation_id ON memory_sources(conversation_id);

-- 2. 对话组表（整组对话打标签归档 - 日记功能）
CREATE TABLE IF NOT EXISTS conversation_groups (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    title VARCHAR(200) NOT NULL,              -- 组标题（日记标题）
    description TEXT,                         -- 描述
    tags TEXT,                                -- JSON数组: ["焦虑", "职业规划"]
    conversation_ids TEXT,                    -- JSON数组: [1,2,3,4] 包含的对话ID
    summary TEXT,                             -- AI生成的摘要
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    is_pinned BOOLEAN DEFAULT 0,              -- 是否置顶
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

-- 索引优化
CREATE INDEX IF NOT EXISTS idx_conversation_groups_user_id ON conversation_groups(user_id);
CREATE INDEX IF NOT EXISTS idx_conversation_groups_created_at ON conversation_groups(created_at);

-- 3. 为对话表添加记忆相关字段（仅在表存在时执行）
-- SQLite不支持条件ALTER TABLE，使用备用方案
PRAGMA foreign_keys=off;

-- 尝试添加列（如果表存在）
-- 注意：如果conversations表不存在，请在应用启动后由SQLAlchemy自动创建
-- 然后手动执行以下ALTER TABLE命令：
-- ALTER TABLE conversations ADD COLUMN topic_tag VARCHAR(50);
-- ALTER TABLE conversations ADD COLUMN memory_extracted BOOLEAN DEFAULT 0;

PRAGMA foreign_keys=on;

-- 4. 星图节点表（如果不存在则创建，用于L2→L3同步）
-- 注意：如果 star_nodes 表已存在，请跳过此部分
CREATE TABLE IF NOT EXISTS star_nodes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    node_type VARCHAR(50) NOT NULL,           -- goal/preference/fact/event
    title VARCHAR(200) NOT NULL,
    description TEXT,
    category VARCHAR(50),
    metadata TEXT,                            -- JSON格式存储额外信息
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_star_nodes_user_id ON star_nodes(user_id);
CREATE INDEX IF NOT EXISTS idx_star_nodes_type ON star_nodes(node_type);
