# -*- coding: utf-8 -*-
"""
星图路由模块

提供用户个人星图相关的API接口：
- GET /star/graph - 获取用户星图数据（节点和边）
- GET /star/node/{node_id} - 获取节点详情
- POST /star/node/{node_id}/expand - 展开子节点

星图基于用户的VIA测评数据构建，展示用户的性格优势图谱
"""

from typing import List, Optional, Dict, Any
from datetime import datetime
from enum import Enum

from fastapi import APIRouter, HTTPException, Depends, Query, status
from pydantic import BaseModel, Field

# 导入数据库和认证
from database.connection import get_db_session
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from middleware.auth_middleware import get_current_user
from utils.response import success_response, error_response, ResponseCode

# 导入模型
from database.models import (
    Assessment, AssessmentResult,
    VirtueCategory, StrengthDefinition
)

# 导入服务层
from services.star_service import StarService

# 创建路由
router = APIRouter(
    tags=["star"],
    responses={
        404: {"description": "节点不存在"},
        400: {"description": "请求参数错误"},
        500: {"description": "服务器内部错误"},
    },
)


# ========== 常量定义 ==========

# VIA 6大美德配置
VIRTUE_CONFIG = {
    "WISDOM": {
        "name": "智慧",
        "name_en": "Wisdom",
        "color": "#4A90D9",  # 天际蓝
        "description": "知识获取与运用的能力"
    },
    "COURAGE": {
        "name": "勇气",
        "name_en": "Courage",
        "color": "#50C878",  # 翠绿
        "description": "面对困难与挑战的决心"
    },
    "HUMANITY": {
        "name": "仁爱",
        "name_en": "Humanity",
        "color": "#FF6B9D",  # 粉红
        "description": "关爱他人与建立关系的能力"
    },
    "JUSTICE": {
        "name": "正义",
        "name_en": "Justice",
        "color": "#F39C12",  # 橙色
        "description": "公平对待他人与维护集体"
    },
    "TEMPERANCE": {
        "name": "节制",
        "name_en": "Temperance",
        "color": "#9B59B6",  # 紫色
        "description": "自我控制与平衡的能力"
    },
    "TRANSCENDENCE": {
        "name": "超越",
        "name_en": "Transcendence",
        "color": "#1ABC9C",  # 青色
        "description": "连接更高意义与美好"
    }
}

# VIA 24项优势映射到美德
STRENGTH_TO_VIRTUE = {
    # 智慧
    "creativity": "WISDOM",
    "curiosity": "WISDOM",
    "judgment": "WISDOM",
    "love_of_learning": "WISDOM",
    "perspective": "WISDOM",
    # 勇气
    "bravery": "COURAGE",
    "perseverance": "COURAGE",
    "honesty": "COURAGE",
    "zest": "COURAGE",
    # 仁爱
    "love": "HUMANITY",
    "kindness": "HUMANITY",
    "social_intelligence": "HUMANITY",
    # 正义
    "teamwork": "JUSTICE",
    "fairness": "JUSTICE",
    "leadership": "JUSTICE",
    # 节制
    "forgiveness": "TEMPERANCE",
    "humility": "TEMPERANCE",
    "prudence": "TEMPERANCE",
    "self_regulation": "TEMPERANCE",
    # 超越
    "appreciation_of_beauty": "TRANSCENDENCE",
    "gratitude": "TRANSCENDENCE",
    "hope": "TRANSCENDENCE",
    "humor": "TRANSCENDENCE",
    "spirituality": "TRANSCENDENCE"
}


# ========== 请求/响应模型 ==========

class NodeType(str, Enum):
    """节点类型"""
    ROOT = "root"           # L1: 用户根节点
    CATEGORY = "category"   # L2: 美德类别
    STRENGTH = "strength"   # L3: 具体优势
    INSIGHT = "insight"     # L4: AI洞察


class RelationType(str, Enum):
    """关系类型"""
    BELONGS_TO = "belongs_to"    # 归属
    LEADS_TO = "leads_to"         # 导致/顺序
    SUGGESTS = "suggests"         # 建议
    RELATES_TO = "relates_to"     # 相关


class StarNode(BaseModel):
    """星图节点"""
    id: str = Field(..., description="节点唯一标识")
    node_type: NodeType = Field(..., description="节点类型")
    title: str = Field(..., description="节点标题")
    description: Optional[str] = Field(None, description="节点描述")
    category: Optional[str] = Field(None, description="所属类别")
    level: int = Field(..., ge=1, le=4, description="层级 1-4")
    parent_id: Optional[str] = Field(None, description="父节点ID")
    
    # 视觉属性
    size: int = Field(40, description="节点大小")
    color: str = Field("#4A90D9", description="节点颜色")
    shape: str = Field("circle", description="节点形状")
    
    # 数据属性
    score: Optional[float] = Field(None, description="得分")
    rank: Optional[int] = Field(None, description="排名")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="扩展数据")


class StarEdge(BaseModel):
    """星图边"""
    id: str = Field(..., description="边唯一标识")
    source: str = Field(..., description="源节点ID")
    target: str = Field(..., description="目标节点ID")
    relation_type: RelationType = Field(..., description="关系类型")
    weight: float = Field(1.0, ge=0, le=1, description="关系强度")
    label: Optional[str] = Field(None, description="边标签")


class CreateEdgeRequest(BaseModel):
    """创建边请求"""
    graph_id: str = Field(..., description="图谱ID")
    source: str = Field(..., description="源节点ID")
    target: str = Field(..., description="目标节点ID")
    relation_type: str = Field("relates_to", description="关系类型")
    weight: float = Field(1.0, description="关系强度")
    label: Optional[str] = Field(None, description="边标签")


class StarGraphResponse(BaseModel):
    """星图响应"""
    graph_id: str = Field(..., description="图谱ID")
    user_id: str = Field(..., description="用户ID")
    root_id: str = Field(..., description="根节点ID")
    nodes: List[StarNode] = Field(default_factory=list, description="节点列表")
    edges: List[StarEdge] = Field(default_factory=list, description="边列表")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="元数据")


class NodeDetailResponse(BaseModel):
    """节点详情响应"""
    node: StarNode = Field(..., description="节点信息")
    children: List[StarNode] = Field(default_factory=list, description="子节点")
    related_memories: List[Dict[str, Any]] = Field(default_factory=list, description="关联记忆")
    ai_suggestions: List[str] = Field(default_factory=list, description="AI建议")


class CreateNodeRequest(BaseModel):
    """创建节点请求"""
    graph_id: str = Field(..., description="星图ID")
    node_type: str = Field(..., description="节点类型")
    title: str = Field(..., description="节点标题")
    description: Optional[str] = Field(None, description="节点描述")
    category: Optional[str] = Field(None, description="所属类别")
    level: int = Field(3, ge=1, le=4, description="层级 1-4")
    parent_id: Optional[str] = Field(None, description="父节点ID")
    size: int = Field(40, description="节点大小")
    color: str = Field("#4A90D9", description="节点颜色")
    shape: str = Field("circle", description="节点形状")
    score: Optional[float] = Field(None, description="得分")
    rank: Optional[int] = Field(None, description="排名")
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict, description="扩展数据")
    is_expanded: bool = Field(False, description="是否展开")
    position_x: Optional[float] = Field(None, description="X坐标")
    position_y: Optional[float] = Field(None, description="Y坐标")


# ========== 辅助函数 ==========

def get_virtue_color(virtue_code: str) -> str:
    """获取美德颜色"""
    return VIRTUE_CONFIG.get(virtue_code, {}).get("color", "#95A5A6")


def get_virtue_code_by_name(name: str) -> str:
    """
    根据中文名称获取美德代码
    
    Args:
        name: 美德中文名
        
    Returns:
        美德英文代码
    """
    name_to_code = {
        "智慧": "WISDOM",
        "智慧与知识": "WISDOM",
        "勇气": "COURAGE",
        "仁爱": "HUMANITY",
        "人道": "HUMANITY",
        "正义": "JUSTICE",
        "节制": "TEMPERANCE",
        "超越": "TRANSCENDENCE",
        "超越性": "TRANSCENDENCE"
    }
    return name_to_code.get(name, name.upper())


def get_virtue_name(virtue_code: str) -> str:
    """获取美德中文名"""
    return VIRTUE_CONFIG.get(virtue_code, {}).get("name", virtue_code)


def calculate_node_size(score: float, min_size: int = 40, max_size: int = 100) -> int:
    """
    根据得分计算节点大小
    
    Args:
        score: 得分 (0-100)
        min_size: 最小尺寸
        max_size: 最大尺寸
    
    Returns:
        计算后的节点大小
    """
    normalized = max(0, min(100, score)) / 100
    return int(min_size + (max_size - min_size) * normalized)


def get_node_shape(node_type: NodeType) -> str:
    """获取节点形状"""
    shape_map = {
        NodeType.ROOT: "star",
        NodeType.CATEGORY: "hexagon",
        NodeType.STRENGTH: "circle",
        NodeType.INSIGHT: "diamond"
    }
    return shape_map.get(node_type, "circle")


# ========== 路由实现 ==========

@router.get("/graph")
async def get_star_graph(
    depth: int = Query(default=3, ge=1, le=4, description="展开深度 1-4"),
    focus_node_id: Optional[str] = Query(default=None, description="聚焦节点ID"),
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
):
    """
    获取用户个人星图数据
    
    基于用户的VIA测评结果构建星图，包含：
    - L1: 用户根节点
    - L2: 6大美德类别节点
    - L3: 24项优势节点（得分决定大小）
    
    Args:
        depth: 展开深度，默认3层
        focus_node_id: 可选，聚焦到特定节点
        current_user: 当前登录用户
        db: 数据库会话
    
    Returns:
        StarGraphResponse: 星图数据（节点和边）
    """
    user_id = current_user["id"]
    graph_id = f"star_{user_id}"
    root_id = f"user_{user_id}"
    
    nodes = []
    edges = []
    
    # 1. 创建根节点 (L1)
    root_node = StarNode(
        id=root_id,
        node_type=NodeType.ROOT,
        title=current_user.get("nickname") or current_user.get("username") or "我的星图",
        description="个人性格优势图谱",
        level=1,
        size=80,
        color="#1E3A5F",  # 深海蓝
        shape=get_node_shape(NodeType.ROOT),
        metadata={
            "user_id": user_id,
            "email": current_user.get("email")
        }
    )
    nodes.append(root_node)
    
    # 2. 查询最新的VIA测评结果
    try:
        # 获取用户最新的已完成测评
        stmt = select(Assessment).where(
            and_(
                Assessment.user_id == user_id,
                Assessment.status == "completed"
            )
        ).order_by(Assessment.completed_at.desc()).limit(1)
        
        result = await db.execute(stmt)
        assessment = result.scalar_one_or_none()
        
        if not assessment:
            # 用户没有测评数据，返回基础结构
            return success_response(
                data={
                    "graph_id": graph_id,
                    "user_id": str(user_id),
                    "root_id": root_id,
                    "nodes": [node.dict() for node in nodes],
                    "edges": [edge.dict() for edge in edges],
                    "metadata": {
                        "has_assessment": False,
                        "message": "请先完成VIA性格优势测评",
                        "total_nodes": len(nodes),
                        "total_edges": len(edges)
                    }
                }
            )
        
        # 获取测评结果详情
        stmt_results = select(AssessmentResult).where(
            AssessmentResult.assessment_id == assessment.id
        ).order_by(AssessmentResult.rank.asc())
        
        result = await db.execute(stmt_results)
        strength_results = result.scalars().all()
        
        if not strength_results:
            return success_response(
                data={
                    "graph_id": graph_id,
                    "user_id": str(user_id),
                    "root_id": root_id,
                    "nodes": [node.dict() for node in nodes],
                    "edges": [edge.dict() for edge in edges],
                    "metadata": {
                        "has_assessment": True,
                        "has_results": False,
                        "message": "测评结果数据不完整",
                        "total_nodes": len(nodes),
                        "total_edges": len(edges)
                    }
                }
            )
        
        # 3. 构建美德类别节点 (L2)
        virtue_nodes = {}
        virtue_scores = {}
        
        # 计算各美德的平均分
        for sr in strength_results:
            # 将中文 category 转换为英文 virtue_code
            virtue_code = get_virtue_code_by_name(sr.category)
            if virtue_code not in virtue_scores:
                virtue_scores[virtue_code] = []
            virtue_scores[virtue_code].append(sr.normalized_score or sr.score)
        
        # 创建美德节点
        for virtue_code, scores in virtue_scores.items():
            avg_score = sum(scores) / len(scores) if scores else 50
            virtue_config = VIRTUE_CONFIG.get(virtue_code, {})
            
            virtue_node_id = f"virtue_{virtue_code.lower()}"
            virtue_node = StarNode(
                id=virtue_node_id,
                node_type=NodeType.CATEGORY,
                title=virtue_config.get("name", virtue_code),
                description=virtue_config.get("description", ""),
                category=virtue_code.lower(),
                level=2,
                parent_id=root_id,
                size=calculate_node_size(avg_score, 50, 80),
                color=virtue_config.get("color", "#95A5A6"),
                shape=get_node_shape(NodeType.CATEGORY),
                score=round(avg_score, 2),
                metadata={
                    "virtue_code": virtue_code,
                    "strengths_count": len(scores),
                    "average_score": round(avg_score, 2)
                }
            )
            virtue_nodes[virtue_code] = virtue_node
            nodes.append(virtue_node)
            
            # 添加根节点到美德节点的边
            edge = StarEdge(
                id=f"edge_{root_id}_{virtue_node_id}",
                source=root_id,
                target=virtue_node_id,
                relation_type=RelationType.BELONGS_TO,
                weight=round(avg_score / 100, 2),
                label="拥有"
            )
            edges.append(edge)
        
        # 4. 构建优势节点 (L3) - 如果深度>=3
        if depth >= 3:
            for sr in strength_results:
                # 将中文 category 转换为英文 virtue_code
                virtue_code = get_virtue_code_by_name(sr.category)
                virtue_node_id = f"virtue_{virtue_code.lower()}"
                
                strength_node_id = f"strength_{sr.dimension_code or sr.id}"
                score = sr.normalized_score or sr.score
                
                strength_node = StarNode(
                    id=strength_node_id,
                    node_type=NodeType.STRENGTH,
                    title=sr.dimension_name,
                    description=sr.interpretation or sr.strengths_description,
                    category=virtue_code.lower(),
                    level=3,
                    parent_id=virtue_node_id,
                    size=calculate_node_size(score, 30, 70),
                    color=get_virtue_color(virtue_code),
                    shape=get_node_shape(NodeType.STRENGTH),
                    score=round(score, 2),
                    rank=sr.rank,
                    metadata={
                        "dimension_code": sr.dimension_code,
                        "percentile": sr.percentile,
                        "development_tips": sr.development_tips,
                        "related_strengths": sr.related_strengths
                    }
                )
                nodes.append(strength_node)
                
                # 添加美德节点到优势节点的边
                edge = StarEdge(
                    id=f"edge_{virtue_node_id}_{strength_node_id}",
                    source=virtue_node_id,
                    target=strength_node_id,
                    relation_type=RelationType.BELONGS_TO,
                    weight=round(score / 100, 2),
                    label="包含"
                )
                edges.append(edge)
        
        # 构建响应
        return success_response(
            data={
                "graph_id": graph_id,
                "user_id": str(user_id),
                "root_id": root_id,
                "nodes": [node.dict() for node in nodes],
                "edges": [edge.dict() for edge in edges],
                "metadata": {
                    "has_assessment": True,
                    "assessment_id": str(assessment.id),
                    "assessment_completed_at": assessment.completed_at.isoformat() if assessment.completed_at else None,
                    "total_nodes": len(nodes),
                    "total_edges": len(edges),
                    "depth": depth,
                    "virtue_count": len(virtue_nodes),
                    "strength_count": len(strength_results) if depth >= 3 else 0
                }
            }
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"构建星图失败: {str(e)}"
        )


@router.get("/node/{node_id}")
async def get_node_detail(
    node_id: str,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
):
    """
    获取星图节点详情
    
    Args:
        node_id: 节点ID
        current_user: 当前登录用户
        db: 数据库会话
    
    Returns:
        NodeDetailResponse: 节点详情
    """
    user_id = current_user["id"]
    
    # 解析节点类型
    if node_id == f"user_{user_id}":
        # 根节点详情
        node = StarNode(
            id=node_id,
            node_type=NodeType.ROOT,
            title=current_user.get("nickname") or current_user.get("username") or "我的星图",
            description="个人性格优势图谱中心",
            level=1,
            size=80,
            color="#1E3A5F",
            shape="star",
            metadata={
                "user_id": user_id,
                "email": current_user.get("email")
            }
        )
        
        # 获取子节点（美德节点）
        children = []
        for virtue_code, config in VIRTUE_CONFIG.items():
            child = StarNode(
                id=f"virtue_{virtue_code.lower()}",
                node_type=NodeType.CATEGORY,
                title=config["name"],
                description=config["description"],
                category=virtue_code.lower(),
                level=2,
                parent_id=node_id,
                size=60,
                color=config["color"],
                shape="hexagon"
            )
            children.append(child)
        
        return success_response(
            data={
                "node": node.dict(),
                "children": [child.dict() for child in children],
                "ai_suggestions": [
                    "查看各美德领域的详细优势分析",
                    "探索优势间的关联与协同效应",
                    "制定基于优势的个人发展计划"
                ]
            }
        )
    
    elif node_id.startswith("virtue_"):
        # 美德节点详情
        virtue_code = node_id.replace("virtue_", "").upper()
        config = VIRTUE_CONFIG.get(virtue_code, {})
        
        node = StarNode(
            id=node_id,
            node_type=NodeType.CATEGORY,
            title=config.get("name", virtue_code),
            description=config.get("description", ""),
            category=virtue_code.lower(),
            level=2,
            parent_id=f"user_{user_id}",
            size=60,
            color=config.get("color", "#95A5A6"),
            shape="hexagon",
            metadata={
                "virtue_code": virtue_code
            }
        )
        
        return success_response(
            data={
                "node": node.dict(),
                "ai_suggestions": [
                    f"探索{config.get('name', '')}领域的具体优势",
                    f"了解如何在日常生活中发挥{config.get('name', '')}",
                    "查看相关的发展建议与资源"
                ]
            }
        )
    
    else:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"节点不存在: {node_id}"
        )


@router.post("/node/{node_id}/expand")
async def expand_node(
    node_id: str,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
):
    """
    展开节点，返回子节点数据
    
    用于懒加载场景，当用户点击"展开"时动态加载子节点
    
    Args:
        node_id: 要展开的节点ID
        current_user: 当前登录用户
        db: 数据库会话
    
    Returns:
        Dict: 包含子节点和边的数据
    """
    user_id = current_user["id"]
    
    # 使用服务层获取子节点
    service = StarService(db)
    children = await service.get_child_nodes(node_id, user_id)
    
    # 更新节点展开状态
    await service.update_expand_state(node_id, user_id, True)
    
    return success_response(
        data={
            "node_id": node_id,
            "children": [
                {
                    "id": child.id,
                    "node_type": child.node_type,
                    "title": child.title,
                    "description": child.description,
                    "category": child.category,
                    "level": child.level,
                    "parent_id": child.parent_id,
                    "size": child.size,
                    "color": child.color,
                    "shape": child.shape,
                    "score": child.score,
                    "rank": child.rank,
                    "metadata": child.metadata,
                    "is_expanded": child.is_expanded
                }
                for child in children
            ],
            "has_more": False
        }
    )


# ========== 星图管理路由 ==========

@router.get("/graphs")
async def get_star_graphs(
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
):
    """获取用户的星图列表"""
    service = StarService(db)
    graphs = await service.get_graphs(current_user["id"])
    return success_response(data=[{
        "id": g.id,
        "name": g.name,
        "type": g.type,
        "source": g.source,
        "is_default": g.is_default,
        "node_count": g.node_count,
        "created_at": g.created_at.isoformat() if g.created_at else None,
        "updated_at": g.updated_at.isoformat() if g.updated_at else None
    } for g in graphs])


@router.post("/graphs")
async def create_star_graph(
    name: str,
    graph_type: str = "scene",
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
):
    """创建新星图"""
    service = StarService(db)
    graph = await service.create_graph(
        user_id=current_user["id"],
        name=name,
        graph_type=graph_type
    )
    return success_response(data={
        "id": graph.id,
        "name": graph.name,
        "type": graph.type,
        "source": graph.source,
        "is_default": graph.is_default,
        "created_at": graph.created_at.isoformat() if graph.created_at else None
    })


@router.get("/graphs/{graph_id}")
async def get_star_graph_detail(
    graph_id: str,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
):
    """获取星图详情（包含节点和边）"""
    service = StarService(db)
    data = await service.get_graph_with_data(graph_id, current_user["id"])
    graph = data["graph"]
    nodes = data["nodes"]
    edges = data["edges"]
    
    # 构建纯字典响应，避免SQLAlchemy对象序列化问题
    result = {
        "id": str(graph.id) if graph.id else None,
        "name": str(graph.name) if graph.name else None,
        "type": str(graph.type) if graph.type else None,
        "source": str(graph.source) if graph.source else None,
        "is_default": bool(graph.is_default) if graph.is_default is not None else False,
        "node_count": int(graph.node_count) if graph.node_count else 0,
        "created_at": graph.created_at.isoformat() if graph.created_at else None,
        "updated_at": graph.updated_at.isoformat() if graph.updated_at else None,
        "nodes": [],
        "edges": []
    }
    
    # 处理节点
    for n in nodes:
        node_data = {
            "id": str(n.id) if n.id else None,
            "node_type": str(n.node_type) if n.node_type else None,
            "title": str(n.title) if n.title else None,
            "description": str(n.description) if n.description else None,
            "category": str(n.category) if n.category else None,
            "level": int(n.level) if n.level else None,
            "parent_id": str(n.parent_id) if n.parent_id else None,
            "size": int(n.size) if n.size else 40,
            "color": str(n.color) if n.color else "#4A90D9",
            "shape": str(n.shape) if n.shape else "circle",
            "score": float(n.score) if n.score else None,
            "rank": int(n.rank) if n.rank else None,
            "metadata": {},
            "is_expanded": bool(n.is_expanded) if n.is_expanded is not None else False,
            "position_x": float(n.position_x) if n.position_x else None,
            "position_y": float(n.position_y) if n.position_y else None
        }
        # 安全获取元数据
        try:
            meta = getattr(n, '_metadata', None) or getattr(n, 'metadata', None)
            if meta and isinstance(meta, dict):
                node_data["metadata"] = meta
        except:
            pass
        result["nodes"].append(node_data)
    
    # 处理边
    for e in edges:
        edge_data = {
            "id": str(e.id) if e.id else None,
            "source": str(e.source) if e.source else None,
            "target": str(e.target) if e.target else None,
            "relation_type": str(e.relation_type) if e.relation_type else None,
            "weight": float(e.weight) if e.weight else 1.0,
            "label": str(e.label) if e.label else None
        }
        result["edges"].append(edge_data)
    
    return success_response(data=result)


@router.put("/graphs/{graph_id}")
async def update_star_graph(
    graph_id: str,
    name: str,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
):
    """更新星图信息"""
    service = StarService(db)
    graph = await service.update_graph(graph_id, current_user["id"], {"name": name})
    return success_response(data={
        "id": graph.id,
        "name": graph.name,
        "updated_at": graph.updated_at.isoformat() if graph.updated_at else None
    })


@router.delete("/graphs/{graph_id}")
async def delete_star_graph(
    graph_id: str,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
):
    """删除星图"""
    service = StarService(db)
    await service.delete_graph(graph_id, current_user["id"])
    return success_response(message="星图已删除")


@router.post("/graphs/{graph_id}/set-default")
async def set_default_star_graph(
    graph_id: str,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
):
    """设置默认星图"""
    service = StarService(db)
    graph = await service.set_default_graph(graph_id, current_user["id"])
    return success_response(data={
        "id": graph.id,
        "name": graph.name,
        "is_default": graph.is_default
    })


@router.post("/graphs/import-via")
async def import_star_graph_from_via(
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
):
    """从VIA测评导入生成主星图"""
    service = StarService(db)
    
    # 获取用户最新的测评
    stmt = select(Assessment).where(
        and_(
            Assessment.user_id == current_user["id"],
            Assessment.status == "completed"
        )
    ).order_by(Assessment.completed_at.desc()).limit(1)
    result = await db.execute(stmt)
    assessment = result.scalar_one_or_none()
    
    if not assessment:
        return error_response(message="请先完成VIA性格优势测评")
    
    graph = await service.import_from_via(current_user["id"], assessment.id)
    return success_response(data={
        "graph_id": graph.id,
        "name": graph.name,
        "node_count": graph.node_count
    })


@router.post("/graphs/{graph_id}/clone")
async def clone_star_graph(
    graph_id: str,
    new_name: str,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
):
    """克隆星图"""
    service = StarService(db)
    new_graph = await service.clone_graph(graph_id, current_user["id"], new_name)
    return success_response(data={
        "id": new_graph.id,
        "name": new_graph.name,
        "node_count": new_graph.node_count
    })


# ========== 节点管理路由 ==========

@router.get("/graphs/{graph_id}/nodes")
async def get_star_nodes(
    graph_id: str,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
):
    """获取星图的所有持久化节点"""
    service = StarService(db)
    nodes = await service.get_nodes(graph_id, current_user["id"])
    return success_response(data=[{
        "id": n.id,
        "node_type": n.node_type,
        "title": n.title,
        "description": n.description,
        "category": n.category,
        "level": n.level,
        "parent_id": n.parent_id,
        "size": n.size,
        "color": n.color,
        "shape": n.shape,
        "score": n.score,
        "rank": n.rank,
        "metadata": n.metadata,
        "is_expanded": n.is_expanded,
        "position_x": n.position_x,
        "position_y": n.position_y
    } for n in nodes])


@router.post("/nodes")
async def create_star_node(
    request: CreateNodeRequest,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
):
    """创建节点（持久化）"""
    service = StarService(db)
    node = await service.create_node(current_user["id"], request.graph_id, {
        "node_type": request.node_type,
        "title": request.title,
        "description": request.description,
        "category": request.category,
        "level": request.level,
        "parent_id": request.parent_id,
        "size": request.size,
        "color": request.color,
        "shape": request.shape,
        "score": request.score,
        "rank": request.rank,
        "metadata": request.metadata or {},
        "is_expanded": request.is_expanded,
        "position_x": request.position_x,
        "position_y": request.position_y
    })
    return success_response(data={
        "id": node.id,
        "title": node.title,
        "node_type": node.node_type,
        "level": node.level
    })


@router.put("/nodes/{node_id}")
async def update_star_node(
    node_id: str,
    update_data: Dict[str, Any],
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
):
    """更新节点信息"""
    service = StarService(db)
    node = await service.update_node(node_id, current_user["id"], update_data)
    return success_response(data={
        "id": node.id,
        "title": node.title,
        "updated_at": node.updated_at.isoformat() if node.updated_at else None
    })


@router.delete("/nodes/{node_id}")
async def delete_star_node(
    node_id: str,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
):
    """删除节点"""
    service = StarService(db)
    await service.delete_node(node_id, current_user["id"])
    return success_response(message="节点已删除")


@router.post("/nodes/{node_id}/expand")
async def expand_star_node(
    node_id: str,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
):
    """展开节点（更新is_expanded=true）"""
    service = StarService(db)
    node = await service.update_expand_state(node_id, current_user["id"], True)
    return success_response(data={"id": node.id, "is_expanded": node.is_expanded})


@router.post("/nodes/{node_id}/collapse")
async def collapse_star_node(
    node_id: str,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
):
    """折叠节点（更新is_expanded=false）"""
    service = StarService(db)
    node = await service.update_expand_state(node_id, current_user["id"], False)
    return success_response(data={"id": node.id, "is_expanded": node.is_expanded})


@router.post("/nodes/{node_id}/move")
async def move_star_node(
    node_id: str,
    x: float,
    y: float,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
):
    """移动节点位置"""
    service = StarService(db)
    node = await service.update_position(node_id, current_user["id"], x, y)
    return success_response(data={
        "id": node.id,
        "position_x": node.position_x,
        "position_y": node.position_y
    })


# ========== 边管理路由 ==========

@router.get("/graphs/{graph_id}/edges")
async def get_star_edges(
    graph_id: str,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
):
    """获取星图的所有边"""
    service = StarService(db)
    edges = await service.get_edges(graph_id, current_user["id"])
    return success_response(data=[{
        "id": e.id,
        "source": e.source,
        "target": e.target,
        "relation_type": e.relation_type,
        "weight": e.weight,
        "label": e.label
    } for e in edges])


@router.post("/edges")
async def create_star_edge(
    request: CreateEdgeRequest,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
):
    """创建边"""
    service = StarService(db)
    edge = await service.create_edge(request.graph_id, current_user["id"], {
        "source": request.source,
        "target": request.target,
        "relation_type": request.relation_type,
        "weight": request.weight,
        "label": request.label
    })
    return success_response(data={
        "id": edge.id,
        "source": edge.source,
        "target": edge.target
    })


@router.delete("/edges/{edge_id}")
async def delete_star_edge(
    edge_id: str,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
):
    """删除边"""
    service = StarService(db)
    await service.delete_edge(edge_id, current_user["id"])
    return success_response(message="边已删除")
