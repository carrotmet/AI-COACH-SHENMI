# -*- coding: utf-8 -*-
"""
测评路由模块

提供测评相关的API接口：
- POST /assessments - 创建测评
- GET /assessments - 获取用户测评列表
- GET /assessments/{id} - 获取测评详情
- GET /assessments/{id}/questions - 获取题目
- POST /assessments/{id}/answers - 提交答案
- POST /assessments/{id}/complete - 完成测评
- GET /assessments/{id}/result - 获取结果
- GET /assessments/{id}/report - 生成报表
"""

from typing import List, Optional, Dict, Any
from datetime import datetime

from fastapi import APIRouter, HTTPException, Depends, Query, status
from pydantic import BaseModel, Field, validator

# 导入认证
from middleware.auth_middleware import get_current_user

# 导入服务
from services.assessment_service import (
    AssessmentService, 
    AssessmentType,
    AssessmentStatus,
    get_assessment_service,
)
from services.report_service import (
    ReportService,
    ReportType,
    get_report_service,
)
from services.scoring_engine import AssessmentResult
from data.via_questions import VIA_QUESTIONS, VIA_QUESTION_OPTIONS


# 创建路由
router = APIRouter(
    tags=["assessments"],
    responses={
        404: {"description": "测评不存在"},
        400: {"description": "请求参数错误"},
        500: {"description": "服务器内部错误"},
    },
)


# ========== 请求/响应模型 ==========

class CreateAssessmentRequest(BaseModel):
    """创建测评请求"""
    type: str = Field(default="via_strengths", description="测评类型")
    language: str = Field(default="zh", description="语言")
    
    @validator('type')
    def validate_type(cls, v):
        allowed = ["via_strengths", "via_strengths_full"]
        if v not in allowed:
            raise ValueError(f"测评类型必须是以下之一: {allowed}")
        return v


class CreateAssessmentResponse(BaseModel):
    """创建测评响应"""
    assessment_id: str
    type: str
    status: str
    total_questions: int
    current_question: int
    created_at: str


class SubmitAnswerRequest(BaseModel):
    """提交答案请求"""
    question_id: int = Field(..., description="题目ID", ge=1, le=24)
    score: int = Field(..., description="得分 1-5", ge=1, le=5)


class SubmitAnswerResponse(BaseModel):
    """提交答案响应"""
    assessment_id: str
    current_question: int
    total_questions: int
    progress_percent: float
    is_completed: bool
    next_question: Optional[Dict[str, Any]] = None
    result_url: Optional[str] = None


class BatchSubmitRequest(BaseModel):
    """批量提交答案请求"""
    answers: List[Dict[str, int]] = Field(..., description="答案列表")


class AssessmentProgressResponse(BaseModel):
    """测评进度响应"""
    assessment_id: str
    status: str
    progress_percent: float
    answered_count: int
    total_count: int
    current_question: int
    last_activity_at: Optional[str] = None


class StrengthResult(BaseModel):
    """优势结果"""
    rank: int
    name: str
    virtue_category: str
    raw_score: float
    normalized_score: float
    percentile: int
    description: str
    icon: str
    color: str


class VirtueResult(BaseModel):
    """美德结果"""
    rank: int
    virtue_code: str
    virtue_name: str
    average_score: float
    normalized_score: float
    percentile: int
    strengths_count: int
    description: str
    icon: str
    color: str


class AssessmentResultResponse(BaseModel):
    """测评结果响应"""
    assessment_id: str
    user_id: Optional[str]
    assessment_type: str
    completed_at: str
    top_strengths: List[StrengthResult]
    virtue_scores: List[VirtueResult]
    dominant_virtue: VirtueResult
    balanced_score: float
    summary: str
    recommendations: List[str]


class AssessmentListItem(BaseModel):
    """测评列表项"""
    id: str
    user_id: Optional[str]
    assessment_type: str
    status: str
    progress_percent: float
    answered_count: int
    total_count: int
    started_at: Optional[str]
    completed_at: Optional[str]
    duration_seconds: int
    result_summary: Optional[Dict[str, Any]] = None


class ReportResponse(BaseModel):
    """报表响应"""
    report_id: str
    report_type: str
    title: str
    content: Dict[str, Any]
    is_premium: bool
    created_at: str
    expires_at: Optional[str] = None


class GenerateReportRequest(BaseModel):
    """生成报表请求"""
    report_type: str = Field(default="quick", description="报表类型")
    
    @validator('report_type')
    def validate_report_type(cls, v):
        allowed = ["quick", "full", "trend"]
        if v not in allowed:
            raise ValueError(f"报表类型必须是以下之一: {allowed}")
        return v


# ========== 依赖注入 ==========

async def get_assessment_service_dep() -> AssessmentService:
    """获取测评服务依赖"""
    return get_assessment_service()


async def get_report_service_dep() -> ReportService:
    """获取报表服务依赖"""
    return get_report_service()


# ========== API路由 ==========

@router.post(
    "",
    response_model=CreateAssessmentResponse,
    status_code=status.HTTP_201_CREATED,
    summary="创建测评",
    description="创建一个新的测评会话"
)
async def create_assessment(
    request: CreateAssessmentRequest,
    service: AssessmentService = Depends(get_assessment_service_dep),
    current_user: dict = Depends(get_current_user),
):
    """
    创建新的测评会话
    
    - **type**: 测评类型 (via_strengths/via_strengths_full)
    - **language**: 语言 (zh/en)
    """
    try:
        assessment_type = AssessmentType(request.type)
        session = await service.create_assessment(
            user_id=str(current_user["id"]),
            assessment_type=assessment_type,
        )
        
        return CreateAssessmentResponse(
            assessment_id=session.id,
            type=session.assessment_type.value,
            status=session.status.value,
            total_questions=len(VIA_QUESTIONS),
            current_question=session.current_question_index + 1,
            created_at=session.started_at.isoformat() if session.started_at else "",
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get(
    "",
    response_model=List[AssessmentListItem],
    summary="获取用户测评列表",
    description="获取当前用户的所有测评记录"
)
async def get_user_assessments(
    status: Optional[str] = Query(None, description="状态筛选"),
    limit: int = Query(10, ge=1, le=100, description="返回数量限制"),
    offset: int = Query(0, ge=0, description="偏移量"),
    service: AssessmentService = Depends(get_assessment_service_dep),
    current_user: dict = Depends(get_current_user),
):
    """
    获取用户的测评历史列表
    
    - **status**: 状态筛选 (pending/in_progress/completed/abandoned/expired)
    - **limit**: 返回数量限制
    - **offset**: 偏移量
    """
    status_filter = None
    if status:
        try:
            status_filter = AssessmentStatus(status)
        except ValueError:
            raise HTTPException(status_code=400, detail=f"无效的状态: {status}")
    
    assessments = await service.get_user_assessments(
        user_id=str(current_user["id"]),
        status=status_filter,
        limit=limit,
        offset=offset,
    )
    
    return [AssessmentListItem(**a) for a in assessments]


@router.get(
    "/{assessment_id}",
    response_model=AssessmentListItem,
    summary="获取测评详情",
    description="获取指定测评的详细信息"
)
async def get_assessment(
    assessment_id: str,
    service: AssessmentService = Depends(get_assessment_service_dep),
):
    """
    获取测评详情
    
    - **assessment_id**: 测评ID
    """
    session = await service.get_assessment(assessment_id)
    if not session:
        raise HTTPException(status_code=404, detail="测评不存在")
    
    data = {
        "id": session.id,
        "user_id": session.user_id,
        "assessment_type": session.assessment_type.value,
        "status": session.status.value,
        "progress_percent": round(session.progress_percent, 1),
        "answered_count": len(session.answers),
        "total_count": len(VIA_QUESTIONS),
        "started_at": session.started_at.isoformat() if session.started_at else None,
        "completed_at": session.completed_at.isoformat() if session.completed_at else None,
        "duration_seconds": session.duration_seconds,
    }
    
    if session.result:
        data["result_summary"] = {
            "top_strengths": [
                {
                    "rank": s.rank,
                    "name": s.strength_name,
                    "score": s.raw_score,
                    "percentile": s.percentile,
                }
                for s in session.result.top_strengths
            ],
            "dominant_virtue": session.result.dominant_virtue.virtue_name,
        }
    
    return AssessmentListItem(**data)


@router.get(
    "/{assessment_id}/questions",
    summary="获取测评题目",
    description="获取测评的题目列表"
)
async def get_questions(
    assessment_id: str,
    from_index: Optional[int] = Query(None, description="起始题号"),
    count: int = Query(1, ge=1, le=24, description="题目数量"),
    service: AssessmentService = Depends(get_assessment_service_dep),
):
    """
    获取测评题目
    
    - **assessment_id**: 测评ID
    - **from_index**: 起始题号（默认从当前进度开始）
    - **count**: 获取题目数量
    """
    session = await service.get_assessment(assessment_id)
    if not session:
        raise HTTPException(status_code=404, detail="测评不存在")
    
    questions = await service.get_questions(assessment_id, from_index, count)
    
    return {
        "assessment_id": assessment_id,
        "current_question": session.current_question_index + 1,
        "total_questions": len(VIA_QUESTIONS),
        "progress_percent": round(session.progress_percent, 1),
        "questions": questions,
        "options": VIA_QUESTION_OPTIONS,
    }


@router.post(
    "/{assessment_id}/answers",
    response_model=SubmitAnswerResponse,
    summary="提交答案",
    description="提交单个题目的答案"
)
async def submit_answer(
    assessment_id: str,
    request: SubmitAnswerRequest,
    service: AssessmentService = Depends(get_assessment_service_dep),
):
    """
    提交答案
    
    - **assessment_id**: 测评ID
    - **question_id**: 题目ID
    - **score**: 得分 1-5
    """
    try:
        result = await service.submit_answer(
            assessment_id=assessment_id,
            question_id=request.question_id,
            score=request.score,
        )
        
        return SubmitAnswerResponse(**result)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post(
    "/{assessment_id}/answers/batch",
    summary="批量提交答案",
    description="批量提交多个题目的答案"
)
async def submit_batch_answers(
    assessment_id: str,
    request: BatchSubmitRequest,
    service: AssessmentService = Depends(get_assessment_service_dep),
):
    """
    批量提交答案
    
    - **assessment_id**: 测评ID
    - **answers**: 答案列表 [{"question_id": 1, "score": 5}, ...]
    """
    try:
        result = await service.submit_batch_answers(
            assessment_id=assessment_id,
            answers=request.answers,
        )
        
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get(
    "/{assessment_id}/progress",
    response_model=AssessmentProgressResponse,
    summary="获取测评进度",
    description="获取测评的当前进度"
)
async def get_progress(
    assessment_id: str,
    service: AssessmentService = Depends(get_assessment_service_dep),
):
    """
    获取测评进度
    
    - **assessment_id**: 测评ID
    """
    progress = await service.get_progress(assessment_id)
    if not progress:
        raise HTTPException(status_code=404, detail="测评不存在")
    
    return AssessmentProgressResponse(**progress)


@router.post(
    "/{assessment_id}/complete",
    response_model=AssessmentResultResponse,
    summary="完成测评",
    description="完成测评并计算结果"
)
async def complete_assessment(
    assessment_id: str,
    service: AssessmentService = Depends(get_assessment_service_dep),
):
    """
    完成测评
    
    - **assessment_id**: 测评ID
    """
    try:
        result = await service.complete_assessment(assessment_id)
        return _convert_result_to_response(result)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get(
    "/{assessment_id}/result",
    response_model=AssessmentResultResponse,
    summary="获取测评结果",
    description="获取测评的完整结果"
)
async def get_result(
    assessment_id: str,
    service: AssessmentService = Depends(get_assessment_service_dep),
):
    """
    获取测评结果
    
    - **assessment_id**: 测评ID
    """
    result = await service.get_result(assessment_id)
    if not result:
        raise HTTPException(status_code=404, detail="测评结果不存在")
    
    return _convert_result_to_response(result)


@router.post(
    "/{assessment_id}/report",
    response_model=ReportResponse,
    summary="生成报表",
    description="生成测评报表"
)
async def generate_report(
    assessment_id: str,
    request: GenerateReportRequest,
    assessment_service: AssessmentService = Depends(get_assessment_service_dep),
    report_service: ReportService = Depends(get_report_service_dep),
    user_id: str = "user_001",  # 实际项目中从JWT Token获取
):
    """
    生成测评报表
    
    - **assessment_id**: 测评ID
    - **report_type**: 报表类型 (quick/full/trend)
    """
    try:
        report_type = ReportType(request.report_type)
        
        if report_type == ReportType.QUICK:
            report = await report_service.generate_quick_report(assessment_id, user_id)
        elif report_type == ReportType.FULL:
            report = await report_service.generate_full_report(assessment_id, user_id)
        elif report_type == ReportType.TREND:
            report = await report_service.generate_trend_report(user_id)
        else:
            raise HTTPException(status_code=400, detail=f"不支持的报表类型: {request.report_type}")
        
        return ReportResponse(
            report_id=report.id,
            report_type=report.report_type.value,
            title=report.title,
            content=report.content,
            is_premium=report.is_premium,
            created_at=report.created_at.isoformat(),
            expires_at=report.expires_at.isoformat() if report.expires_at else None,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get(
    "/{assessment_id}/report/{report_id}",
    response_model=ReportResponse,
    summary="获取报表",
    description="获取已生成的报表"
)
async def get_report(
    assessment_id: str,
    report_id: str,
    report_service: ReportService = Depends(get_report_service_dep),
):
    """
    获取报表
    
    - **assessment_id**: 测评ID
    - **report_id**: 报表ID
    """
    report = await report_service.get_report(report_id)
    if not report:
        raise HTTPException(status_code=404, detail="报表不存在")
    
    return ReportResponse(
        report_id=report.id,
        report_type=report.report_type.value,
        title=report.title,
        content=report.content,
        is_premium=report.is_premium,
        created_at=report.created_at.isoformat(),
        expires_at=report.expires_at.isoformat() if report.expires_at else None,
    )


@router.delete(
    "/{assessment_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="删除测评",
    description="删除指定的测评记录"
)
async def delete_assessment(
    assessment_id: str,
    service: AssessmentService = Depends(get_assessment_service_dep),
):
    """
    删除测评
    
    - **assessment_id**: 测评ID
    """
    success = await service.delete_assessment(assessment_id)
    if not success:
        raise HTTPException(status_code=404, detail="测评不存在")
    
    return None


@router.post(
    "/{assessment_id}/abandon",
    summary="放弃测评",
    description="放弃当前进行的测评"
)
async def abandon_assessment(
    assessment_id: str,
    service: AssessmentService = Depends(get_assessment_service_dep),
):
    """
    放弃测评
    
    - **assessment_id**: 测评ID
    """
    success = await service.abandon_assessment(assessment_id)
    if not success:
        raise HTTPException(status_code=400, detail="无法放弃测评")
    
    return {"message": "测评已放弃"}


# ========== 辅助函数 ==========

def _convert_result_to_response(result: AssessmentResult) -> AssessmentResultResponse:
    """
    将AssessmentResult转换为响应模型
    
    Args:
        result: 测评结果
    
    Returns:
        响应模型
    """
    # 转换优势结果
    top_strengths = []
    for s in result.top_strengths:
        top_strengths.append(StrengthResult(
            rank=s.rank,
            name=s.strength_name,
            virtue_category=s.virtue_category,
            raw_score=s.raw_score,
            normalized_score=s.normalized_score,
            percentile=s.percentile,
            description=s.description,
            icon=s.icon,
            color=s.color,
        ))
    
    # 转换美德结果
    virtue_scores = []
    for v in result.virtue_scores:
        virtue_scores.append(VirtueResult(
            rank=v.rank,
            virtue_code=v.virtue_code,
            virtue_name=v.virtue_name,
            average_score=v.average_score,
            normalized_score=v.normalized_score,
            percentile=v.percentile,
            strengths_count=v.strengths_count,
            description=v.description,
            icon=v.icon,
            color=v.color,
        ))
    
    # 转换主导美德
    dominant = result.dominant_virtue
    dominant_virtue = VirtueResult(
        rank=dominant.rank,
        virtue_code=dominant.virtue_code,
        virtue_name=dominant.virtue_name,
        average_score=dominant.average_score,
        normalized_score=dominant.normalized_score,
        percentile=dominant.percentile,
        strengths_count=dominant.strengths_count,
        description=dominant.description,
        icon=dominant.icon,
        color=dominant.color,
    )
    
    return AssessmentResultResponse(
        assessment_id=result.assessment_id,
        user_id=result.user_id,
        assessment_type=result.assessment_type,
        completed_at=result.completed_at.isoformat(),
        top_strengths=top_strengths,
        virtue_scores=virtue_scores,
        dominant_virtue=dominant_virtue,
        balanced_score=result.balanced_score,
        summary=result.summary,
        recommendations=result.recommendations,
    )
