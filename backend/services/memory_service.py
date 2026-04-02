# -*- coding: utf-8 -*-
"""
记忆服务层 - 实现四层记忆模型

功能：
1. 记忆提取 (L1→L2): 从对话提取关键事实
2. 语义检索: 基于向量相似度搜索相关记忆
3. 同步星图 (L2→L3): 将记忆映射为星图节点
4. 对话组管理: 整组对话打标签归档（日记功能）
"""

from typing import List, Dict, Optional, Any
from datetime import datetime
import asyncio

from sqlalchemy import select, insert, text
from sqlalchemy.ext.asyncio import AsyncSession

from config.mem0_config import get_mem0
from database.connection import async_session


class MemoryService:
    """
    记忆管理服务 - 四层记忆模型的实现层
    
    职责：
    - L1→L2: 从原始对话提取关键事实
    - L2→L3: 将关键事实映射为星图节点
    - 动态检索: 基于语义相似度唤醒相关记忆
    - 对话组管理: 整组对话打标签归档（日记）
    """
    
    def __init__(self):
        self.mem0 = get_mem0()
    
    # ============================================================
    # 用法1: 记忆提取与存储 (L1 → L2)
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
                        text("""
                            INSERT INTO memory_sources 
                            (memory_id, conversation_id, extraction_confidence, created_at)
                            VALUES (:memory_id, :conversation_id, :confidence, :created_at)
                        """),
                        {
                            "memory_id": memory.get("id"),
                            "conversation_id": int(conversation_id),
                            "confidence": memory.get("score", 0.0),
                            "created_at": datetime.utcnow().isoformat()
                        }
                    )
                
                # 标记对话已提取
                await db.execute(
                    text("UPDATE conversations SET memory_extracted = 1 WHERE id = :id"),
                    {"id": int(conversation_id)}
                )
                await db.commit()
            
            return result.get("memories", [])
            
        except Exception as e:
            print(f"[MemoryService] 记忆提取失败: {e}")
            return []
    
    # ============================================================
    # 用法2: 语义检索（RAI "回忆中" 阶段）
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
        
        RAI Badge "回忆中..."阶段的核心调用
        
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
    # 用法3: 记忆同步到星图 (L2 → L3)
    # ============================================================
    
    async def sync_memories_to_star_nodes(
        self,
        user_id: str,
        memory_ids: Optional[List[str]] = None
    ) -> List[Dict]:
        """
        将提取的记忆同步为星图节点
        
        Returns:
            创建的节点列表
        """
        created_nodes = []
        
        try:
            # 获取用户的记忆
            if memory_ids:
                memories = []
                for mid in memory_ids:
                    mem = self.mem0.get(memory_id=mid, user_id=user_id)
                    if mem:
                        memories.append(mem)
            else:
                memories = self.mem0.get_all(user_id=user_id)
                memories = memories.get("results", []) if isinstance(memories, dict) else []
            
            # 分类映射为星图节点
            async with async_session() as db:
                for mem in memories:
                    content = mem.get("memory", "")
                    if not content:
                        continue
                    
                    # 根据内容判断节点类型
                    node_type = self._classify_memory_type(content)
                    title = self._generate_node_title(content)
                    
                    # 检查是否已存在相同内容的节点
                    existing = await db.execute(
                        text("SELECT id FROM star_nodes WHERE user_id = :user_id AND title = :title"),
                        {"user_id": int(user_id), "title": title}
                    )
                    if existing.fetchone():
                        continue
                    
                    # 创建星图节点
                    result = await db.execute(
                        text("""
                            INSERT INTO star_nodes 
                            (user_id, node_type, title, description, category, metadata, created_at, updated_at)
                            VALUES (:user_id, :node_type, :title, :description, :category, :metadata, :created_at, :updated_at)
                        """),
                        {
                            "user_id": int(user_id),
                            "node_type": node_type,
                            "title": title,
                            "description": content,
                            "category": node_type,
                            "metadata": json.dumps({
                                "memory_id": mem.get("id"),
                                "source": "mem0_extraction",
                                "created_at": mem.get("created_at")
                            }),
                            "created_at": datetime.utcnow().isoformat(),
                            "updated_at": datetime.utcnow().isoformat()
                        }
                    )
                    await db.commit()
                    
                    created_nodes.append({
                        "id": result.lastrowid,
                        "type": node_type,
                        "title": title,
                        "memory_id": mem.get("id")
                    })
            
            return created_nodes
            
        except Exception as e:
            print(f"[MemoryService] 同步星图失败: {e}")
            return []
    
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
        if len(content) <= 20:
            return content
        return content[:20] + "..."
    
    # ============================================================
    # 用法4: 对话组日记管理
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
        创建标签化的对话组（日记功能）
        
        Args:
            user_id: 用户ID
            title: 组标题（日记标题）
            description: 描述
            tags: 标签列表（如 ["焦虑", "考研", "突破"]）
            conversation_ids: 包含的对话ID列表
            summary: AI生成的摘要
        """
        async with async_session() as db:
            result = await db.execute(
                text("""
                    INSERT INTO conversation_groups 
                    (user_id, title, description, tags, conversation_ids, summary, created_at, updated_at, is_pinned)
                    VALUES (:user_id, :title, :description, :tags, :conversation_ids, :summary, :created_at, :updated_at, 0)
                """),
                {
                    "user_id": int(user_id),
                    "title": title,
                    "description": description,
                    "tags": json.dumps(tags),
                    "conversation_ids": json.dumps(conversation_ids),
                    "summary": summary,
                    "created_at": datetime.utcnow().isoformat(),
                    "updated_at": datetime.utcnow().isoformat()
                }
            )
            await db.commit()
            group_id = result.lastrowid
            
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
    
    async def get_conversation_groups(
        self,
        user_id: str,
        tag: Optional[str] = None
    ) -> List[Dict]:
        """获取对话组列表（可按标签筛选）"""
        async with async_session() as db:
            if tag:
                # 使用 JSON 包含查询
                result = await db.execute(
                    text("""
                        SELECT * FROM conversation_groups 
                        WHERE user_id = :user_id 
                        AND json_extract(tags, '$') LIKE :tag_pattern
                        ORDER BY created_at DESC
                    """),
                    {"user_id": int(user_id), "tag_pattern": f'%"{tag}"%'}
                )
            else:
                result = await db.execute(
                    text("""
                        SELECT * FROM conversation_groups 
                        WHERE user_id = :user_id 
                        ORDER BY created_at DESC
                    """),
                    {"user_id": int(user_id)}
                )
            
            rows = result.fetchall()
            return [
                {
                    "id": row.id,
                    "title": row.title,
                    "description": row.description,
                    "tags": json.loads(row.tags) if row.tags else [],
                    "summary": row.summary,
                    "conversation_ids": json.loads(row.conversation_ids) if row.conversation_ids else [],
                    "is_pinned": row.is_pinned,
                    "created_at": row.created_at
                }
                for row in rows
            ]
    
    async def get_group_detail(self, group_id: int, user_id: str) -> Optional[Dict]:
        """获取对话组详情"""
        async with async_session() as db:
            result = await db.execute(
                text("""
                    SELECT * FROM conversation_groups 
                    WHERE id = :group_id AND user_id = :user_id
                """),
                {"group_id": group_id, "user_id": int(user_id)}
            )
            row = result.fetchone()
            if not row:
                return None
            
            return {
                "id": row.id,
                "title": row.title,
                "description": row.description,
                "tags": json.loads(row.tags) if row.tags else [],
                "summary": row.summary,
                "conversation_ids": json.loads(row.conversation_ids) if row.conversation_ids else [],
                "is_pinned": row.is_pinned,
                "created_at": row.created_at,
                "updated_at": row.updated_at
            }
    
    async def update_group(
        self,
        group_id: int,
        user_id: str,
        title: Optional[str] = None,
        description: Optional[str] = None,
        tags: Optional[List[str]] = None,
        is_pinned: Optional[bool] = None
    ) -> bool:
        """更新对话组"""
        updates = []
        params = {"group_id": group_id, "user_id": int(user_id)}
        
        if title is not None:
            updates.append("title = :title")
            params["title"] = title
        if description is not None:
            updates.append("description = :description")
            params["description"] = description
        if tags is not None:
            updates.append("tags = :tags")
            params["tags"] = json.dumps(tags)
        if is_pinned is not None:
            updates.append("is_pinned = :is_pinned")
            params["is_pinned"] = 1 if is_pinned else 0
        
        if not updates:
            return True
        
        updates.append("updated_at = :updated_at")
        params["updated_at"] = datetime.utcnow().isoformat()
        
        async with async_session() as db:
            await db.execute(
                text(f"""
                    UPDATE conversation_groups 
                    SET {', '.join(updates)}
                    WHERE id = :group_id AND user_id = :user_id
                """),
                params
            )
            await db.commit()
            return True
    
    async def delete_group(self, group_id: int, user_id: str) -> bool:
        """删除对话组"""
        async with async_session() as db:
            result = await db.execute(
                text("""
                    DELETE FROM conversation_groups 
                    WHERE id = :group_id AND user_id = :user_id
                """),
                {"group_id": group_id, "user_id": int(user_id)}
            )
            await db.commit()
            return result.rowcount > 0


import json
