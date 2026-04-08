# -*- coding: utf-8 -*-
"""
星图业务服务层

提供星图的CRUD操作、节点管理、边管理等核心业务逻辑
"""

import uuid
from typing import List, Optional, Dict, Any
from datetime import datetime

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, delete, update
from fastapi import HTTPException, status

from database.models import StarGraph, StarNode, StarEdge


class StarService:
    """星图服务类"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    # ========== 星图管理 ==========
    
    async def create_graph(
        self, 
        user_id: int, 
        name: str, 
        graph_type: str = "main", 
        source: str = "manual",
        is_default: bool = False
    ) -> StarGraph:
        """创建新星图"""
        graph = StarGraph(
            id=str(uuid.uuid4()),
            user_id=user_id,
            name=name,
            type=graph_type,
            source=source,
            is_default=is_default
        )
        self.db.add(graph)
        await self.db.commit()
        await self.db.refresh(graph)
        return graph
    
    async def get_graphs(self, user_id: int) -> List[StarGraph]:
        """获取用户的所有星图"""
        stmt = select(StarGraph).where(StarGraph.user_id == user_id)
        result = await self.db.execute(stmt)
        return result.scalars().all()
    
    async def get_graph(self, graph_id: str, user_id: int) -> Optional[StarGraph]:
        """获取星图详情"""
        stmt = select(StarGraph).where(
            and_(StarGraph.id == graph_id, StarGraph.user_id == user_id)
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()
    
    async def get_default_graph(self, user_id: int) -> Optional[StarGraph]:
        """获取用户的默认星图"""
        stmt = select(StarGraph).where(
            and_(StarGraph.user_id == user_id, StarGraph.is_default == True)
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()
    
    async def update_graph(self, graph_id: str, user_id: int, update_data: Dict[str, Any]) -> StarGraph:
        """更新星图信息"""
        graph = await self.get_graph(graph_id, user_id)
        if not graph:
            raise HTTPException(status_code=404, detail="星图不存在")
        
        for key, value in update_data.items():
            if hasattr(graph, key) and key != 'id':
                setattr(graph, key, value)
        
        graph.updated_at = datetime.now()
        await self.db.commit()
        await self.db.refresh(graph)
        return graph
    
    async def delete_graph(self, graph_id: str, user_id: int) -> bool:
        """删除星图（级联删除所有节点和边）"""
        graph = await self.get_graph(graph_id, user_id)
        if not graph:
            raise HTTPException(status_code=404, detail="星图不存在")
        
        await self.db.delete(graph)
        await self.db.commit()
        return True
    
    async def set_default_graph(self, graph_id: str, user_id: int) -> StarGraph:
        """设置默认星图"""
        # 先取消其他星图的默认状态
        stmt = update(StarGraph).where(
            and_(StarGraph.user_id == user_id, StarGraph.is_default == True)
        ).values(is_default=False)
        await self.db.execute(stmt)
        
        # 设置新的默认星图
        graph = await self.get_graph(graph_id, user_id)
        if not graph:
            raise HTTPException(status_code=404, detail="星图不存在")
        
        graph.is_default = True
        await self.db.commit()
        await self.db.refresh(graph)
        return graph
    
    # ========== 节点管理 ==========
    
    async def create_node(self, user_id: int, graph_id: str, node_data: Dict[str, Any]) -> StarNode:
        """创建节点（持久化）"""
        # 验证星图存在且属于当前用户
        graph = await self.get_graph(graph_id, user_id)
        if not graph:
            raise HTTPException(status_code=404, detail="星图不存在")
        
        # 如果指定了parent_id，验证父节点存在
        parent_id = node_data.get("parent_id")
        if parent_id:
            parent = await self.get_node(parent_id, user_id)
            if not parent:
                raise HTTPException(status_code=404, detail="父节点不存在")
        
        node = StarNode(
            id=str(uuid.uuid4()),
            user_id=user_id,
            graph_id=graph_id,
            node_type=node_data.get("node_type", "goal"),
            title=node_data.get("title", "未命名节点"),
            description=node_data.get("description"),
            category=node_data.get("category"),
            level=node_data.get("level", 3),
            parent_id=parent_id,
            size=node_data.get("size", 40),
            color=node_data.get("color", "#4A90D9"),
            shape=node_data.get("shape", "circle"),
            score=node_data.get("score"),
            rank=node_data.get("rank"),
            _metadata=node_data.get("metadata", {}),
            is_expanded=node_data.get("is_expanded", False),
            position_x=node_data.get("position_x"),
            position_y=node_data.get("position_y")
        )
        self.db.add(node)
        
        # 更新星图节点计数
        graph.node_count += 1
        
        await self.db.commit()
        await self.db.refresh(node)
        return node
    
    async def get_nodes(self, graph_id: str, user_id: int) -> List[StarNode]:
        """获取星图的所有节点（持久化节点）"""
        # 验证星图权限
        graph = await self.get_graph(graph_id, user_id)
        if not graph:
            raise HTTPException(status_code=404, detail="星图不存在")
        
        stmt = select(StarNode).where(
            and_(StarNode.graph_id == graph_id, StarNode.user_id == user_id)
        )
        result = await self.db.execute(stmt)
        return result.scalars().all()
    
    async def get_node(self, node_id: str, user_id: int) -> Optional[StarNode]:
        """获取节点详情"""
        stmt = select(StarNode).where(
            and_(StarNode.id == node_id, StarNode.user_id == user_id)
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()
    
    async def get_child_nodes(self, parent_id: str, user_id: int) -> List[StarNode]:
        """获取子节点列表"""
        stmt = select(StarNode).where(
            and_(StarNode.parent_id == parent_id, StarNode.user_id == user_id)
        )
        result = await self.db.execute(stmt)
        return result.scalars().all()
    
    async def update_node(self, node_id: str, user_id: int, update_data: Dict[str, Any]) -> StarNode:
        """更新节点信息"""
        node = await self.get_node(node_id, user_id)
        if not node:
            raise HTTPException(status_code=404, detail="节点不存在")
        
        # 不允许修改的字段
        restricted_fields = {'id', 'user_id', 'graph_id', 'created_at'}
        
        for key, value in update_data.items():
            if hasattr(node, key) and key not in restricted_fields:
                setattr(node, key, value)
        
        node.updated_at = datetime.now()
        await self.db.commit()
        await self.db.refresh(node)
        return node
    
    async def delete_node(self, node_id: str, user_id: int) -> bool:
        """删除节点（级联删除子节点）"""
        node = await self.get_node(node_id, user_id)
        if not node:
            raise HTTPException(status_code=404, detail="节点不存在")
        
        # 递归删除子节点
        await self._delete_children_recursive(node_id, user_id)
        
        # 删除节点相关的边
        await self._delete_node_edges(node_id)
        
        # 更新星图节点计数
        graph = await self.get_graph(node.graph_id, user_id)
        if graph:
            graph.node_count = max(0, graph.node_count - 1)
        
        # 删除节点
        await self.db.delete(node)
        await self.db.commit()
        return True
    
    async def _delete_children_recursive(self, parent_id: str, user_id: int):
        """递归删除子节点"""
        stmt = select(StarNode).where(
            and_(StarNode.parent_id == parent_id, StarNode.user_id == user_id)
        )
        result = await self.db.execute(stmt)
        children = result.scalars().all()
        
        for child in children:
            await self._delete_children_recursive(child.id, user_id)
            await self._delete_node_edges(child.id)
            await self.db.delete(child)
    
    async def _delete_node_edges(self, node_id: str):
        """删除节点相关的所有边"""
        # 删除以该节点为source或target的边
        stmt = delete(StarEdge).where(
            or_(StarEdge.source == node_id, StarEdge.target == node_id)
        )
        await self.db.execute(stmt)
    
    async def update_expand_state(self, node_id: str, user_id: int, is_expanded: bool) -> StarNode:
        """更新节点展开状态"""
        return await self.update_node(node_id, user_id, {"is_expanded": is_expanded})
    
    async def update_position(self, node_id: str, user_id: int, x: float, y: float) -> StarNode:
        """更新节点位置"""
        return await self.update_node(node_id, user_id, {"position_x": x, "position_y": y})
    
    async def batch_update_positions(self, user_id: int, positions: List[Dict[str, Any]]) -> bool:
        """批量更新节点位置"""
        for pos in positions:
            node_id = pos.get("node_id")
            x = pos.get("x")
            y = pos.get("y")
            if node_id and x is not None and y is not None:
                await self.update_position(node_id, user_id, x, y)
        return True
    
    # ========== 边管理 ==========
    
    async def create_edge(self, graph_id: str, user_id: int, edge_data: Dict[str, Any]) -> StarEdge:
        """创建边"""
        # 验证星图权限
        graph = await self.get_graph(graph_id, user_id)
        if not graph:
            raise HTTPException(status_code=404, detail="星图不存在")
        
        # 验证源节点和目标节点都存在且已持久化
        source_id = edge_data.get("source")
        target_id = edge_data.get("target")
        
        source_node = await self.get_node(source_id, user_id)
        target_node = await self.get_node(target_id, user_id)
        
        if not source_node or not target_node:
            raise HTTPException(status_code=404, detail="源节点或目标节点不存在")
        
        # 检查是否已存在相同边
        relation_type = edge_data.get("relation_type", "relates_to")
        existing = await self._check_edge_exists(source_id, target_id, relation_type)
        if existing:
            raise HTTPException(status_code=400, detail="相同关系的边已存在")
        
        edge = StarEdge(
            id=str(uuid.uuid4()),
            graph_id=graph_id,
            source=source_id,
            target=target_id,
            relation_type=relation_type,
            weight=edge_data.get("weight", 1.0),
            label=edge_data.get("label")
        )
        self.db.add(edge)
        await self.db.commit()
        await self.db.refresh(edge)
        return edge
    
    async def _check_edge_exists(self, source: str, target: str, relation_type: str) -> bool:
        """检查边是否已存在"""
        stmt = select(StarEdge).where(
            and_(
                StarEdge.source == source,
                StarEdge.target == target,
                StarEdge.relation_type == relation_type
            )
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none() is not None
    
    async def get_edges(self, graph_id: str, user_id: int) -> List[StarEdge]:
        """获取星图的所有边"""
        # 验证星图权限
        graph = await self.get_graph(graph_id, user_id)
        if not graph:
            raise HTTPException(status_code=404, detail="星图不存在")
        
        stmt = select(StarEdge).where(StarEdge.graph_id == graph_id)
        result = await self.db.execute(stmt)
        return result.scalars().all()
    
    async def get_node_edges(self, node_id: str, user_id: int, direction: str = "both") -> List[StarEdge]:
        """获取节点的关联边
        
        Args:
            node_id: 节点ID
            user_id: 用户ID
            direction: 方向 - "out"(出边), "in"(入边), "both"(双向)
        """
        # 验证节点权限
        node = await self.get_node(node_id, user_id)
        if not node:
            raise HTTPException(status_code=404, detail="节点不存在")
        
        if direction == "out":
            stmt = select(StarEdge).where(StarEdge.source == node_id)
        elif direction == "in":
            stmt = select(StarEdge).where(StarEdge.target == node_id)
        else:  # both
            from sqlalchemy import or_
            stmt = select(StarEdge).where(
                or_(StarEdge.source == node_id, StarEdge.target == node_id)
            )
        
        result = await self.db.execute(stmt)
        return result.scalars().all()
    
    async def delete_edge(self, edge_id: str, user_id: int) -> bool:
        """删除边"""
        stmt = select(StarEdge).where(StarEdge.id == edge_id)
        result = await self.db.execute(stmt)
        edge = result.scalar_one_or_none()
        
        if not edge:
            raise HTTPException(status_code=404, detail="边不存在")
        
        # 验证权限（通过星图间接验证）
        graph = await self.get_graph(edge.graph_id, user_id)
        if not graph:
            raise HTTPException(status_code=403, detail="无权操作")
        
        await self.db.delete(edge)
        await self.db.commit()
        return True
    
    # ========== VIA测评导入 ==========
    
    async def import_from_via(self, user_id: int, assessment_id: int, name: str = "我的主星图") -> StarGraph:
        """从VIA测评导入生成主星图"""
        from database.models import Assessment, AssessmentResult
        
        # 获取测评数据
        stmt = select(Assessment).where(
            and_(Assessment.id == assessment_id, Assessment.user_id == user_id)
        )
        result = await self.db.execute(stmt)
        assessment = result.scalar_one_or_none()
        
        if not assessment:
            raise HTTPException(status_code=404, detail="测评不存在")
        
        # 检查是否已存在默认星图
        existing_default = await self.get_default_graph(user_id)
        if existing_default:
            # 删除旧的默认星图
            await self.delete_graph(existing_default.id, user_id)
        
        # 创建主星图
        graph = await self.create_graph(
            user_id=user_id,
            name=name,
            graph_type="main",
            source="via",
            is_default=True
        )
        
        # 创建根节点
        root_node = await self.create_node(user_id, graph.id, {
            "node_type": "root",
            "title": "我的星图",
            "description": "个人性格优势图谱",
            "level": 1,
            "size": 80,
            "color": "#1E3A5F",
            "shape": "star",
            "is_expanded": True
        })
        
        # 获取测评结果
        stmt = select(AssessmentResult).where(
            AssessmentResult.assessment_id == assessment_id
        ).order_by(AssessmentResult.rank.asc())
        result = await self.db.execute(stmt)
        strength_results = result.scalars().all()
        
        # 按美德分组计算平均分
        from routers.star import VIRTUE_CONFIG, get_virtue_code_by_name
        virtue_scores = {}
        for sr in strength_results:
            virtue_code = get_virtue_code_by_name(sr.category)
            if virtue_code not in virtue_scores:
                virtue_scores[virtue_code] = []
            virtue_scores[virtue_code].append(sr.normalized_score or sr.score)
        
        # 创建美德类别节点（L2）
        virtue_nodes = {}
        for virtue_code, scores in virtue_scores.items():
            avg_score = sum(scores) / len(scores) if scores else 50
            config = VIRTUE_CONFIG.get(virtue_code, {})
            
            virtue_node = await self.create_node(user_id, graph.id, {
                "node_type": "category",
                "title": config.get("name", virtue_code),
                "description": config.get("description", ""),
                "category": virtue_code.lower(),
                "level": 2,
                "parent_id": root_node.id,
                "size": int(50 + 30 * avg_score / 100),
                "color": config.get("color", "#95A5A6"),
                "shape": "hexagon",
                "score": round(avg_score, 2),
                "is_expanded": False
            })
            virtue_nodes[virtue_code] = virtue_node
            
            # 创建边（根节点 -> 美德节点）
            await self.create_edge(graph.id, user_id, {
                "source": root_node.id,
                "target": virtue_node.id,
                "relation_type": "belongs_to",
                "weight": round(avg_score / 100, 2),
                "label": "拥有"
            })
        
        # 创建优势节点（L3）
        for sr in strength_results:
            virtue_code = get_virtue_code_by_name(sr.category)
            virtue_node = virtue_nodes.get(virtue_code)
            if not virtue_node:
                continue
            
            score = sr.normalized_score or sr.score
            config = VIRTUE_CONFIG.get(virtue_code, {})
            
            strength_node = await self.create_node(user_id, graph.id, {
                "node_type": "strength",
                "title": sr.dimension_name,
                "description": sr.interpretation or sr.strengths_description,
                "category": virtue_code.lower(),
                "level": 3,
                "parent_id": virtue_node.id,
                "size": int(30 + 40 * score / 100),
                "color": config.get("color", "#95A5A6"),
                "shape": "circle",
                "score": round(score, 2),
                "rank": sr.rank,
                "metadata": {
                    "dimension_code": sr.dimension_code,
                    "percentile": sr.percentile,
                    "development_tips": sr.development_tips,
                    "related_strengths": sr.related_strengths
                }
            })
            
            # 创建边（美德节点 -> 优势节点）
            await self.create_edge(graph.id, user_id, {
                "source": virtue_node.id,
                "target": strength_node.id,
                "relation_type": "belongs_to",
                "weight": round(score / 100, 2),
                "label": "包含"
            })
        
        await self.db.commit()
        return graph
    
    # ========== 辅助方法 ==========
    
    async def get_graph_with_data(self, graph_id: str, user_id: int) -> Dict[str, Any]:
        """获取完整的星图数据（包含节点和边）"""
        graph = await self.get_graph(graph_id, user_id)
        if not graph:
            raise HTTPException(status_code=404, detail="星图不存在")
        
        nodes = await self.get_nodes(graph_id, user_id)
        edges = await self.get_edges(graph_id, user_id)
        
        return {
            "graph": graph,
            "nodes": nodes,
            "edges": edges
        }
    
    async def clone_graph(self, graph_id: str, user_id: int, new_name: str) -> StarGraph:
        """克隆星图"""
        # 获取原星图数据
        data = await self.get_graph_with_data(graph_id, user_id)
        original_graph = data["graph"]
        nodes = data["nodes"]
        edges = data["edges"]
        
        # 创建新星图
        new_graph = await self.create_graph(
            user_id=user_id,
            name=new_name,
            graph_type=original_graph.type,
            source="manual"
        )
        
        # 节点ID映射（旧ID -> 新ID）
        node_id_map = {}
        
        # 复制节点
        for node in nodes:
            new_node_data = {
                "node_type": node.node_type,
                "title": node.title,
                "description": node.description,
                "category": node.category,
                "level": node.level,
                "parent_id": node_id_map.get(node.parent_id) if node.parent_id else None,
                "size": node.size,
                "color": node.color,
                "shape": node.shape,
                "score": node.score,
                "rank": node.rank,
                "metadata": node._metadata or {},
                "is_expanded": node.is_expanded,
                "position_x": node.position_x,
                "position_y": node.position_y
            }
            new_node = await self.create_node(user_id, new_graph.id, new_node_data)
            node_id_map[node.id] = new_node.id
        
        # 复制边
        for edge in edges:
            new_edge_data = {
                "source": node_id_map.get(edge.source),
                "target": node_id_map.get(edge.target),
                "relation_type": edge.relation_type,
                "weight": edge.weight,
                "label": edge.label
            }
            if new_edge_data["source"] and new_edge_data["target"]:
                await self.create_edge(new_graph.id, user_id, new_edge_data)
        
        return new_graph


# 导入or_用于边的查询
from sqlalchemy import or_