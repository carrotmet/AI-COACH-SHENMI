# Mem0 记忆模块集成实施文档

**版本**: v1.0  
**日期**: 2026-03-16  
**关联文档**: [深觅 AI Coach 产品设计报告](./design0311.md)

---

## 1. 架构定位

Mem0 是深觅长记忆架构的核心组件，实现**"双轨记忆+动态检索"**设计范式，将用户相关信息划分为四个层次：

```
┌─────────────────────────────────────────────────────────────────────────┐
│                          四层记忆模型                                    │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  L1 原始对话层  →  conversations 表（原始消息，会话级查询）              │
│       ↓                                                                 │
│  L2 提取事实层  →  Mem0 自动提取的关键事实（用户属性、目标、偏好）       │
│       ↓                                                                 │
│  L3 结构化记忆层 →  Star Nodes（目标、任务、习惯、偏好等实体节点）       │
│       ↓                                                                 │
│  L4 洞察推理层  →  Star Insights（AI生成的模式识别、趋势预测）          │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

Mem0 负责 L1→L2→L3 的转化过程，支持**基于相关性的智能检索**，而非简单的时间倒序。

---

## 2. 技术栈选型（与整体架构一致）

| 组件 | 选型 | 说明 |
|------|------|------|
| **Mem0** | `mem0ai` | 核心记忆管理框架，内置提取/去重/摘要/关联 |
| **向量存储** | **Chroma** (本地) | 零配置、单文件、与 SQLite 同目录 |
| **嵌入模型** | `sentence-transformers/all-MiniLM-L6-v2` | 本地运行，384维，轻量高效 |
| **LLM提取** | LiteLLM 网关 | 复用现有配置，GPT-4o-mini 用于记忆提取 |

**不采用 Pinecone/Qdrant 云端方案的原因**：
- MVP阶段保持完全本地化，零外部依赖
- 与现有 SQLite 单文件架构一致
- 用户隐私优先（记忆不上传云端）

---

## 3. 数据模型

### 3.1 Mem0 核心表（自动管理）

Mem0 自动创建以下表结构（位于 `./data/mem0_chroma/`）：

```
data/mem0_chroma/
├── chroma.sqlite3          # Chroma 向量存储
└── ...                     # 索引文件
```

### 3.2 业务层扩展表（SQLite）

在现有 `ai_coach.db` 中新增：

```sql
-- 记忆与原始对话的关联映射
CREATE TABLE memory_sources (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    memory_id VARCHAR(255) NOT NULL,          -- Mem0 返回的记忆ID
    conversation_id INTEGER NOT NULL,         -- 关联对话ID
    message_id INTEGER,                       -- 关联消息ID（可选）
    extraction_confidence FLOAT,              -- 提取置信度
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (conversation_id) REFERENCES conversations(id) ON DELETE CASCADE
);

-- 对话组（整组对话打标签归档）
CREATE TABLE conversation_groups (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    title VARCHAR(200) NOT NULL,              -- 组标题（AI生成或用户指定）
    description TEXT,                         -- 描述
    tags JSON,                                -- ["焦虑", "职业规划"]
    conversation_ids JSON,                    -- [1,2,3,4] 包含的对话ID
    summary TEXT,                             -- AI生成的摘要
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    is_pinned BOOLEAN DEFAULT 0,              -- 是否置顶
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

-- 为对话添加主题标签（用于快速分类）
ALTER TABLE conversations ADD COLUMN topic_tag VARCHAR(50);
ALTER TABLE conversations ADD COLUMN memory_extracted BOOLEAN DEFAULT 0;  -- 是否已提取记忆
```

---

## 4. 实施步骤

### Step 1: 依赖安装

```bash
# backend/requirements.txt 追加
mem0ai>=0.1.21
chromadb>=0.4.18
sentence-transformers>=2.5.0
```

### Step 2: Mem0 配置模块

```python
# backend/config/mem0_config.py
import os
from mem0 import Memory

# Mem0 配置（完全本地化）
MEM0_CONFIG = {
    "vector_store": {
        "provider": "chroma",
        "config": {
            "path": "./data/mem0_chroma",
            "collection_name": "shenmi_memories"
        }
    },
    "llm": {
        "provider": "litellm",  # 复用现有 LiteLLM 网关
        "config": {
            "model": "gpt-4o-mini",
            "temperature": 0.1,   # 提取记忆需要稳定输出
            "max_tokens": 500
        }
    },
    "embedder": {
        "provider": "huggingface",
        "config": {
            "model": "sentence-transformers/all-MiniLM-L6-v2",
            "embedding_dims": 384
        }
    }
}

# 全局内存实例（单例模式）
_mem0_instance = None

def get_mem0() -> Memory:
    """获取 Mem0 实例（单例）"""
    global _mem0_instance
    if _mem0_instance is None:
        # 确保目录存在
        os.makedirs("./data/mem0_chroma", exist_ok=True)
        _mem0_instance = Memory.from_config(MEM0_CONFIG)
    return _mem0_instance
```

### Step 3: 记忆服务层

```python
# backend/services/memory_service.py
from typing import List, Dict, Optional, Any
from datetime import datetime
import asyncio

from mem0 import Memory
from sqlalchemy import select, insert
from sqlalchemy.ext.asyncio import AsyncSession

from config.mem0_config import get_mem0
from database.connection import async_session
from database.models import Conversation, conversation_groups, memory_sources

class MemoryService:
    """
    记忆管理服务 - 四层记忆模型的实现层
    
    职责：
    - L1→L2: 从原始对话提取关键事实
    - L2→L3: 将关键事实映射为星图节点
    - 动态检索: 基于语义相似度唤醒相关记忆
    - 对话组管理: 整组对话打标签归档
    """
    
    def __init__(self):
        self.mem0 = get_mem0()
    
    # ============================================================
    # L1 → L2: 记忆提取与存储
    # ============================================================
    
    async def extract_and_store_memories(
        self,
        user_id: str,
        conversation_id: str,
        messages: List[Dict[str, str]]
    ) -> List[Dict]:
        """
        从对话中提取关键信息并存储到 Mem0
        
        Args:
            user_id: 用户ID
            conversation_id: 对话ID
            messages: 消息列表 [{"role": "user", "content": "..."}, ...]
            
        Returns:
            提取的记忆列表
        """
        try:
            # Mem0 自动提取关键信息
            result = self.mem0.add(
                messages=messages,
                user_id=user_id,
                metadata={
                    "conversation_id": conversation_id,
                    "extracted_at": datetime.utcnow().isoformat(),
                    "type": "conversation_extract"
                }
            )
            
            # 记录关联映射到数据库
            async with async_session() as db:
                for memory in result.get("memories", []):
                    await db.execute(
                        insert(memory_sources).values(
                            memory_id=memory.get("id"),
                            conversation_id=int(conversation_id),
                            extraction_confidence=memory.get("score", 0.0)
                        )
                    )
                
                # 标记对话已提取
                await db.execute(
                    "UPDATE conversations SET memory_extracted = 1 WHERE id = :id",
                    {"id": int(conversation_id)}
                )
                await db.commit()
            
            return result.get("memories", [])
            
        except Exception as e:
            print(f"[MemoryService] 记忆提取失败: {e}")
            return []
    
    # ============================================================
    # L2 → L3: 记忆映射到星图节点
    # ============================================================
    
    async def sync_memories_to_star_nodes(
        self,
        user_id: str,
        memory_ids: Optional[List[str]] = None
    ):
        """
        将提取的记忆同步为星图节点
        
        由 StarService 调用，将记忆转化为可视化节点
        """
        from services.star_service import StarService
        
        star_service = StarService()
        
        # 获取用户的所有记忆（或指定记忆）
        if memory_ids:
            memories = []
            for mid in memory_ids:
                mem = self.mem0.get(memory_id=mid, user_id=user_id)
                if mem:
                    memories.append(mem)
        else:
            # 获取全部（实际应分页）
            memories = self.mem0.get_all(user_id=user_id)
        
        # 分类映射为星图节点
        for mem in memories:
            content = mem.get("memory", "")
            
            # 根据内容判断节点类型
            node_type = self._classify_memory_type(content)
            
            # 创建或更新星图节点
            await star_service.create_node_from_memory(
                user_id=user_id,
                memory_id=mem.get("id"),
                node_type=node_type,
                title=self._generate_node_title(content),
                description=content,
                metadata={
                    "memory_id": mem.get("id"),
                    "source": "mem0_extraction",
                    "created_at": mem.get("created_at")
                }
            )
    
    def _classify_memory_type(self, content: str) -> str:
        """根据内容分类记忆类型"""
        keywords = {
            "goal": ["目标", "想", "计划", "打算", "希望"],
            "preference": ["喜欢", "偏好", "习惯", "总是", "经常"],
            "fact": ["我叫", "我是", "我在", "我的"],
            "event": ["发生了", "昨天", "上周", "有一次"]
        }
        
        for node_type, words in keywords.items():
            if any(w in content for w in words):
                return node_type
        return "fact"
    
    def _generate_node_title(self, content: str) -> str:
        """生成节点标题（摘要）"""
        # 取前20字或第一句
        if len(content) <= 20:
            return content
        return content[:20] + "..."
    
    # ============================================================
    # 动态检索: 基于语义相似度
    # ============================================================
    
    async def retrieve_relevant_memories(
        self,
        user_id: str,
        query: str,
        limit: int = 5,
        memory_type: Optional[str] = None
    ) -> List[Dict]:
        """
        检索与当前查询相关的记忆（四层模型中的"动态检索"）
        
        这是 RAI Badge "回忆中..."阶段的核心调用
        
        Args:
            user_id: 用户ID
            query: 当前用户输入（用于语义匹配）
            limit: 返回记忆数量
            memory_type: 筛选特定类型（goal/preference/fact）
        """
        try:
            # Mem0 向量语义搜索
            results = self.mem0.search(
                query=query,
                user_id=user_id,
                limit=limit * 2  # 多取一些用于过滤
            )
            
            memories = results.get("results", [])
            
            # 按类型过滤
            if memory_type:
                memories = [
                    m for m in memories 
                    if self._classify_memory_type(m.get("memory", "")) == memory_type
                ]
            
            # 按相关性分数排序，取前N
            memories.sort(key=lambda x: x.get("score", 0), reverse=True)
            return memories[:limit]
            
        except Exception as e:
            print(f"[MemoryService] 记忆检索失败: {e}")
            return []
    
    # ============================================================
    # 对话组管理（整组对话打标签）
    # ============================================================
    
    async def create_conversation_group(
        self,
        user_id: str,
        title: str,
        description: str,
        tags: List[str],
        conversation_ids: List[int],
        summary: str = ""
    ) -> int:
        """
        创建标签化的对话组
        
        Args:
            user_id: 用户ID
            title: 组标题
            description: 描述
            tags: 标签列表（如 ["焦虑", "职业规划"])
            conversation_ids: 包含的对话ID列表
            summary: AI生成的摘要
        """
        async with async_session() as db:
            result = await db.execute(
                insert(conversation_groups).values(
                    user_id=int(user_id),
                    title=title,
                    description=description,
                    tags=tags,
                    conversation_ids=conversation_ids,
                    summary=summary
                )
            )
            await db.commit()
            group_id = result.inserted_primary_key[0]
            
            # 同步到 Mem0 便于语义检索
            self.mem0.add(
                messages=f"对话组: {title}\n摘要: {summary}\n标签: {', '.join(tags)}",
                user_id=user_id,
                metadata={
                    "type": "conversation_group",
                    "group_id": group_id,
                    "tags": tags
                }
            )
            
            return group_id
    
    async def get_groups_by_tag(
        self,
        user_id: str,
        tag: str
    ) -> List[Dict]:
        """按标签获取对话组"""
        async with async_session() as db:
            result = await db.execute(
                select(conversation_groups).where(
                    conversation_groups.c.user_id == int(user_id),
                    conversation_groups.c.tags.contains([tag])
                ).order_by(conversation_groups.c.created_at.desc())
            )
            rows = result.fetchall()
            return [
                {
                    "id": row.id,
                    "title": row.title,
                    "tags": row.tags,
                    "summary": row.summary,
                    "created_at": row.created_at.isoformat()
                }
                for row in rows
            ]
```

### Step 4: 对话服务集成（LangGraph 节点）

```python
# backend/services/chat_service.py (修改)

from services.memory_service import MemoryService

class ChatService:
    def __init__(self):
        self.memory_service = MemoryService()
        self.llm = get_litellm_service()
    
    async def process_message(
        self,
        user_id: str,
        conversation_id: str,
        message: str,
        stream: bool = False
    ) -> AsyncGenerator[str, None]:
        """
        处理用户消息 - 集成 Mem0 的完整流程
        
        LangGraph 状态机节点：
        1. 输入接收 → 2. 记忆检索(回忆中) → 3. 意图识别 → 4. 回复生成
        """
        
        # ========== Node 2: 记忆检索（"回忆中..."） ==========
        relevant_memories = await self.memory_service.retrieve_relevant_memories(
            user_id=user_id,
            query=message,
            limit=5
        )
        
        # 构建记忆上下文
        memory_context = ""
        if relevant_memories:
            memory_context = "\n\n[用户历史相关信息]\n"
            for i, mem in enumerate(relevant_memories, 1):
                memory_context += f"{i}. {mem['memory']}\n"
        
        # ========== Node 3: 意图识别 ==========
        intent_result = await self._identify_intent(message)
        
        # ========== Node 4: 回复生成 ==========
        prompt = f"""你是深觅 AI Coach，一位专业的个人成长教练。

{memory_context}

用户当前输入：{message}

意图识别：{intent_result['intent']} (置信度: {intent_result['confidence']})

请基于用户的历史背景提供个性化、有深度的回复。如果用户表达了新的目标、偏好或重要信息，请在回复中自然确认，以便后续跟进。
"""
        
        # 流式生成回复
        full_response = ""
        async for token in self.llm.stream_chat(prompt):
            full_response += token
            if stream:
                yield token
        
        # ========== 异步：记忆提取（不阻塞回复） ==========
        asyncio.create_task(
            self._async_extract_memories(
                user_id=user_id,
                conversation_id=conversation_id,
                user_message=message,
                ai_response=full_response
            )
        )
        
        if not stream:
            yield full_response
    
    async def _async_extract_memories(
        self,
        user_id: str,
        conversation_id: str,
        user_message: str,
        ai_response: str
    ):
        """异步提取记忆（后台执行）"""
        messages = [
            {"role": "user", "content": user_message},
            {"role": "assistant", "content": ai_response}
        ]
        
        # 提取并存储
        memories = await self.memory_service.extract_and_store_memories(
            user_id=user_id,
            conversation_id=conversation_id,
            messages=messages
        )
        
        # 同步到星图节点（L2 → L3）
        if memories:
            await self.memory_service.sync_memories_to_star_nodes(
                user_id=user_id,
                memory_ids=[m["id"] for m in memories]
            )
    
    async def _identify_intent(self, message: str) -> Dict:
        """意图识别（简化版）"""
        # 可扩展为调用 LLM 或规则引擎
        intents = {
            "目标设定": ["目标", "想", "计划"],
            "情绪支持": ["焦虑", "压力", "难过"],
            "知识获取": ["什么是", "如何", "为什么"],
        }
        
        for intent, keywords in intents.items():
            if any(kw in message for kw in keywords):
                return {"intent": intent, "confidence": 0.8}
        
        return {"intent": "通用对话", "confidence": 0.5}
```

### Step 5: API 路由

```python
# backend/routers/memories.py
from fastapi import APIRouter, Depends, Query
from typing import List, Optional

from services.memory_service import MemoryService
from middleware.auth_middleware import get_current_user
from utils.response import success_response

router = APIRouter(prefix="/api/v1/memories", tags=["memories"])

def get_memory_service() -> MemoryService:
    return MemoryService()

@router.get("/search")
async def search_memories(
    query: str = Query(..., description="搜索查询"),
    limit: int = Query(5, ge=1, le=20),
    memory_type: Optional[str] = Query(None, description="筛选类型: goal/preference/fact/event"),
    current_user: dict = Depends(get_current_user),
    service: MemoryService = Depends(get_memory_service)
):
    """
    语义搜索记忆
    
    用于 RAI Badge 的"回忆中"阶段，根据用户输入检索相关历史
    """
    results = await service.retrieve_relevant_memories(
        user_id=str(current_user["id"]),
        query=query,
        limit=limit,
        memory_type=memory_type
    )
    return success_response(data={
        "query": query,
        "memories": results,
        "total": len(results)
    })

@router.get("/all")
async def get_all_memories(
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    current_user: dict = Depends(get_current_user),
    service: MemoryService = Depends(get_memory_service)
):
    """获取用户的全部记忆（分页）"""
    memories = service.mem0.get_all(
        user_id=str(current_user["id"]),
        limit=limit,
        offset=offset
    )
    return success_response(data=memories)

@router.delete("/{memory_id}")
async def delete_memory(
    memory_id: str,
    current_user: dict = Depends(get_current_user),
    service: MemoryService = Depends(get_memory_service)
):
    """删除特定记忆"""
    service.mem0.delete(
        memory_id=memory_id,
        user_id=str(current_user["id"])
    )
    return success_response(message="记忆已删除")

# ==================== 对话组管理 ====================

from pydantic import BaseModel

class CreateGroupRequest(BaseModel):
    title: str
    description: str = ""
    tags: List[str]
    conversation_ids: List[int]
    summary: str = ""

@router.post("/groups")
async def create_conversation_group(
    request: CreateGroupRequest,
    current_user: dict = Depends(get_current_user),
    service: MemoryService = Depends(get_memory_service)
):
    """创建标签化的对话组"""
    group_id = await service.create_conversation_group(
        user_id=str(current_user["id"]),
        title=request.title,
        description=request.description,
        tags=request.tags,
        conversation_ids=request.conversation_ids,
        summary=request.summary
    )
    return success_response(data={"group_id": group_id})

@router.get("/groups")
async def get_conversation_groups(
    tag: Optional[str] = Query(None, description="按标签筛选"),
    current_user: dict = Depends(get_current_user),
    service: MemoryService = Depends(get_memory_service)
):
    """获取对话组列表"""
    if tag:
        groups = await service.get_groups_by_tag(
            user_id=str(current_user["id"]),
            tag=tag
        )
    else:
        # 获取全部（简化版）
        from database.connection import async_session
        from sqlalchemy import select
        from database.models import conversation_groups
        
        async with async_session() as db:
            result = await db.execute(
                select(conversation_groups).where(
                    conversation_groups.c.user_id == int(current_user["id"])
                ).order_by(conversation_groups.c.created_at.desc())
            )
            rows = result.fetchall()
            groups = [
                {
                    "id": r.id,
                    "title": r.title,
                    "tags": r.tags,
                    "summary": r.summary,
                    "created_at": r.created_at.isoformat()
                }
                for r in rows
            ]
    
    return success_response(data=groups)
```

### Step 6: 前端集成

```javascript
// frontend/js/api.js 追加记忆相关API

const memoryAPI = {
    /**
     * 语义搜索记忆（RAI Badge "回忆中"阶段调用）
     */
    search(query, limit = 5, memoryType = null) {
        const params = new URLSearchParams({ query, limit: String(limit) });
        if (memoryType) params.append('memory_type', memoryType);
        return request(`/memories/search?${params}`);
    },

    /**
     * 获取全部记忆
     */
    getAll(limit = 20, offset = 0) {
        return request(`/memories/all?limit=${limit}&offset=${offset}`);
    },

    /**
     * 删除记忆
     */
    delete(memoryId) {
        return request(`/memories/${memoryId}`, { method: 'DELETE' });
    },

    /**
     * 创建对话组
     */
    createGroup(data) {
        return request('/memories/groups', {
            method: 'POST',
            body: data
        });
    },

    /**
     * 获取对话组
     */
    getGroups(tag = null) {
        const url = tag ? `/memories/groups?tag=${tag}` : '/memories/groups';
        return request(url);
    }
};

// 在 api 对象中注册
const api = {
    // ... 其他API
    memory: memoryAPI,
    // ...
};
```

---

## 5. 与现有模块的集成关系

### 5.1 与深潜模块（对话）

```
用户输入
    ↓
RAI Badge "回忆中..." → api.memory.search(query)
    ↓
检索到的记忆注入 Prompt
    ↓
LLM 生成回复
    ↓
异步提取新记忆 → api.memory.extract()
```

### 5.2 与观己模块（星图）

```
Mem0 提取的记忆 (L2)
    ↓
MemoryService.sync_memories_to_star_nodes()
    ↓
StarService.create_node_from_memory()
    ↓
星图节点 (L3: goal/preference/fact/event)
    ↓
Star Graph 可视化
```

### 5.3 与追觅模块（计划）

```
计划生成时
    ↓
检索目标相关记忆 ("用户之前提到想考研")
    ↓
结合记忆上下文生成个性化计划
```

---

## 6. 存储目录结构

```
data/
├── ai_coach.db              # 主数据库（SQLite）
│   ├── conversations        # 原始对话 (L1)
│   ├── conversation_groups  # 对话组
│   └── memory_sources       # 记忆来源映射
│
└── mem0_chroma/             # Mem0 向量存储
    ├── chroma.sqlite3
    └── ...
```

---

## 7. 部署检查清单

- [ ] `pip install mem0ai chromadb sentence-transformers`
- [ ] 创建 `data/mem0_chroma/` 目录
- [ ] 执行数据库迁移（新增表）
- [ ] 配置 `MEM0_CONFIG` 中的 LiteLLM 参数
- [ ] 注册 `memory_router` 到 FastAPI
- [ ] 前端添加 `api.memory` 调用
- [ ] 测试对话流程中的记忆提取与检索

---

## 8. 关键设计决策

| 决策点 | 选择 | 理由 |
|--------|------|------|
| 向量库 | Chroma (本地) | 零配置、隐私优先、与 SQLite 同架构 |
| 嵌入模型 | all-MiniLM-L6-v2 (本地) | 384维、轻量、无需外部API |
| 提取触发 | 异步后台 | 不阻塞对话响应，用户体验优先 |
| 同步策略 | 记忆→星图实时同步 | 保持 L2/L3 一致性 |
| 对话组 | SQLite 存储 + Mem0 索引 | 结构化查询 + 语义检索互补 |

---

**下一步**: 实施 Step 1-3（安装依赖、配置 Mem0、实现 MemoryService）
