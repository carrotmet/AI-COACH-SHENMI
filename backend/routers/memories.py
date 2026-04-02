# -*- coding: utf-8 -*-
"""
记忆系统 API 路由

功能：
- GET  /api/v1/memories/search     - 语义搜索记忆（RAI "回忆中"）
- GET  /api/v1/memories/all        - 获取全部记忆
- DEL  /api/v1/memories/{id}       - 删除记忆
- POST /api/v1/memories/groups     - 创建对话组（日记）
- GET  /api/v1/memories/groups     - 获取对话组列表
- GET  /api/v1/memories/groups/{id}- 获取对话组详情
- PUT  /api/v1/memories/groups/{id}- 更新对话组
- DEL  /api/v1/memories/groups/{id}- 删除对话组
"""

from fastapi import APIRouter, Depends, Query, Path
from typing import List, Optional
from pydantic import BaseModel, Field

from services.memory_service import MemoryService
from middleware.auth_middleware import get_current_user
from utils.response import success_response, error_response, ResponseCode

router = APIRouter(prefix="/api/v1/memories", tags=["记忆系统"])


def get_memory_service() -> MemoryService:
    return MemoryService()


# ============================================================
# 用法2: 语义检索（RAI "回忆中"）
# ============================================================

@router.get("/search")
async def search_memories(
    query: str = Query(..., description="搜索查询"),
    limit: int = Query(5, ge=1, le=20, description="返回数量"),
    memory_type: Optional[str] = Query(None, description="筛选类型: goal/preference/fact/event"),
    current_user: dict = Depends(get_current_user),
    service: MemoryService = Depends(get_memory_service)
):
    """
    语义搜索记忆
    
    用于 RAI Badge 的"回忆中"阶段，根据用户输入检索相关历史
    """
    try:
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
    except Exception as e:
        return error_response(message=f"搜索失败: {str(e)}")


@router.get("/all")
async def get_all_memories(
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    current_user: dict = Depends(get_current_user),
    service: MemoryService = Depends(get_memory_service)
):
    """获取用户的全部记忆（分页）"""
    try:
        memories = service.mem0.get_all(
            user_id=str(current_user["id"]),
            limit=limit,
            offset=offset
        )
        # 统一返回格式
        if isinstance(memories, dict):
            memories = memories.get("results", [])
        return success_response(data=memories)
    except Exception as e:
        return error_response(message=f"获取失败: {str(e)}")


@router.delete("/{memory_id}")
async def delete_memory(
    memory_id: str = Path(..., description="记忆ID"),
    current_user: dict = Depends(get_current_user),
    service: MemoryService = Depends(get_memory_service)
):
    """删除特定记忆"""
    try:
        service.mem0.delete(
            memory_id=memory_id,
            user_id=str(current_user["id"])
        )
        return success_response(message="记忆已删除")
    except Exception as e:
        return error_response(message=f"删除失败: {str(e)}")


# ============================================================
# 用法4: 对话组日记管理
# ============================================================

class CreateGroupRequest(BaseModel):
    """创建对话组请求"""
    title: str = Field(..., min_length=1, max_length=200, description="组标题")
    description: str = Field(default="", description="描述")
    tags: List[str] = Field(default=[], description="标签列表")
    conversation_ids: List[int] = Field(..., description="包含的对话ID列表")
    summary: str = Field(default="", description="AI生成的摘要")


class UpdateGroupRequest(BaseModel):
    """更新对话组请求"""
    title: Optional[str] = Field(default=None, max_length=200)
    description: Optional[str] = Field(default=None)
    tags: Optional[List[str]] = Field(default=None)
    is_pinned: Optional[bool] = Field(default=None)


@router.post("/groups")
async def create_conversation_group(
    request: CreateGroupRequest,
    current_user: dict = Depends(get_current_user),
    service: MemoryService = Depends(get_memory_service)
):
    """创建标签化的对话组（日记功能）"""
    try:
        group_id = await service.create_conversation_group(
            user_id=str(current_user["id"]),
            title=request.title,
            description=request.description,
            tags=request.tags,
            conversation_ids=request.conversation_ids,
            summary=request.summary
        )
        return success_response(data={"group_id": group_id}, message="创建成功")
    except Exception as e:
        return error_response(message=f"创建失败: {str(e)}")


@router.get("/groups")
async def get_conversation_groups(
    tag: Optional[str] = Query(None, description="按标签筛选"),
    current_user: dict = Depends(get_current_user),
    service: MemoryService = Depends(get_memory_service)
):
    """获取对话组列表（日记列表）"""
    try:
        groups = await service.get_conversation_groups(
            user_id=str(current_user["id"]),
            tag=tag
        )
        return success_response(data=groups)
    except Exception as e:
        return error_response(message=f"获取失败: {str(e)}")


@router.get("/groups/{group_id}")
async def get_group_detail(
    group_id: int = Path(..., description="组ID"),
    current_user: dict = Depends(get_current_user),
    service: MemoryService = Depends(get_memory_service)
):
    """获取对话组详情"""
    try:
        group = await service.get_group_detail(
            group_id=group_id,
            user_id=str(current_user["id"])
        )
        if not group:
            return error_response(code=ResponseCode.NOT_FOUND, message="对话组不存在")
        return success_response(data=group)
    except Exception as e:
        return error_response(code=ResponseCode.INTERNAL_ERROR, message=f"获取失败: {str(e)}")


@router.put("/groups/{group_id}")
async def update_conversation_group(
    group_id: int = Path(..., description="组ID"),
    request: UpdateGroupRequest = ...,
    current_user: dict = Depends(get_current_user),
    service: MemoryService = Depends(get_memory_service)
):
    """更新对话组"""
    try:
        success = await service.update_group(
            group_id=group_id,
            user_id=str(current_user["id"]),
            title=request.title,
            description=request.description,
            tags=request.tags,
            is_pinned=request.is_pinned
        )
        if success:
            return success_response(message="更新成功")
        return error_response(code=ResponseCode.NOT_FOUND, message="对话组不存在")
    except Exception as e:
        return error_response(code=ResponseCode.INTERNAL_ERROR, message=f"更新失败: {str(e)}")


@router.delete("/groups/{group_id}")
async def delete_conversation_group(
    group_id: int = Path(..., description="组ID"),
    current_user: dict = Depends(get_current_user),
    service: MemoryService = Depends(get_memory_service)
):
    """删除对话组"""
    try:
        success = await service.delete_group(
            group_id=group_id,
            user_id=str(current_user["id"])
        )
        if success:
            return success_response(message="删除成功")
        return error_response(code=ResponseCode.NOT_FOUND, message="对话组不存在")
    except Exception as e:
        return error_response(code=ResponseCode.INTERNAL_ERROR, message=f"删除失败: {str(e)}")


# ============================================================
# 用法3: 记忆同步到星图
# ============================================================

@router.post("/sync-to-star")
async def sync_memories_to_star(
    memory_ids: Optional[List[str]] = None,
    current_user: dict = Depends(get_current_user),
    service: MemoryService = Depends(get_memory_service)
):
    """
    将记忆同步到星图节点（L2→L3）
    
    Args:
        memory_ids: 指定记忆ID列表，为空则同步全部
    """
    try:
        nodes = await service.sync_memories_to_star_nodes(
            user_id=str(current_user["id"]),
            memory_ids=memory_ids
        )
        return success_response(
            data={"created_nodes": nodes, "count": len(nodes)},
            message=f"成功创建 {len(nodes)} 个星图节点"
        )
    except Exception as e:
        return error_response(message=f"同步失败: {str(e)}")
