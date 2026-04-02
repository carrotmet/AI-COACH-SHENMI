# -*- coding: utf-8 -*-
"""
测评服务模块

负责测评的生命周期管理：
- 创建测评会话
- 保存答题记录
- 计算测评结果
- 获取测评历史
"""

import uuid
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from enum import Enum

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from database.connection import async_session
from database.models import Assessment, AssessmentResult, AssessmentResponse, AssessmentStatus as DBAssessmentStatus

from services.scoring_engine import ScoringEngine, get_scoring_engine, AssessmentResult as ScoringResult
from data.via_questions import VIA_QUESTIONS, ASSESSMENT_CONFIG


class AssessmentStatus(str, Enum):
    """测评状态"""
    PENDING = "pending"  # 待开始
    IN_PROGRESS = "in_progress"  # 进行中
    COMPLETED = "completed"  # 已完成
    ABANDONED = "abandoned"  # 已放弃
    EXPIRED = "expired"  # 已过期


class AssessmentType(str, Enum):
    """测评类型"""
    VIA_STRENGTHS = "via_strengths"  # VIA简化版
    VIA_STRENGTHS_FULL = "via_strengths_full"  # VIA完整版


@dataclass
class AssessmentSession:
    """测评会话"""
    id: str  # 数据库自增ID的字符串形式
    user_id: Optional[str]
    assessment_type: AssessmentType
    status: AssessmentStatus
    
    # 进度信息
    current_question_index: int
    answers: Dict[str, int] = field(default_factory=dict)  # {strength_key: score}
    progress_percent: float = 0.0
    
    # 时间信息
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    last_activity_at: Optional[datetime] = None
    duration_seconds: int = 0
    
    # 结果
    result: Optional[ScoringResult] = None
    
    def __post_init__(self):
        if self.started_at is None:
            self.started_at = datetime.now()
        if self.last_activity_at is None:
            self.last_activity_at = datetime.now()


@dataclass
class AnswerSubmission:
    """答案提交"""
    question_id: int
    strength_key: str
    score: int  # 1-5
    answered_at: datetime = field(default_factory=datetime.now)


class AssessmentService:
    """
    测评服务
    
    管理测评的完整生命周期，数据持久化到数据库
    """
    
    # 测评过期时间（小时）
    EXPIRY_HOURS = 24
    
    # 内存缓存（用于快速访问）
    _assessments: Dict[str, AssessmentSession] = {}
    
    def __init__(self):
        """初始化测评服务"""
        self.scoring_engine = get_scoring_engine()
    
    async def create_assessment(
        self, 
        user_id: Optional[str] = None,
        assessment_type: AssessmentType = AssessmentType.VIA_STRENGTHS,
        _metadata: Optional[Dict[str, Any]] = None
    ) -> AssessmentSession:
        """
        创建新的测评会话，并持久化到数据库
        
        Args:
            user_id: 用户ID（可选，未登录用户可为空）
            assessment_type: 测评类型
            _metadata: 额外元数据
        
        Returns:
            新创建的测评会话
        """
        # 解析用户ID
        db_user_id = int(user_id) if user_id and user_id.isdigit() else 1
        
        # 创建数据库记录
        async with async_session() as db:
            db_assessment = Assessment(
                user_id=db_user_id,
                assessment_type=assessment_type.value,
                title=f"VIA性格优势测评",
                description="基于VIA性格优势分类的测评",
                status=DBAssessmentStatus.IN_PROGRESS,
                version="1.0",
                started_at=datetime.now(),
                valid_until=datetime.now() + timedelta(days=365),
            )
            db.add(db_assessment)
            await db.commit()
            await db.refresh(db_assessment)
            
            # 使用数据库自增ID作为会话ID
            assessment_id = str(db_assessment.id)
        
        # 创建会话对象
        session = AssessmentSession(
            id=assessment_id,
            user_id=user_id,
            assessment_type=assessment_type,
            status=AssessmentStatus.IN_PROGRESS,
            current_question_index=0,
            started_at=datetime.now(),
            last_activity_at=datetime.now(),
        )
        
        # 保存到内存缓存
        self._assessments[assessment_id] = session
        
        return session
    
    async def get_assessment(self, assessment_id: str) -> Optional[AssessmentSession]:
        """
        获取测评会话（优先从内存，不存在则从数据库恢复）
        
        Args:
            assessment_id: 测评ID
        
        Returns:
            测评会话，如果不存在返回None
        """
        # 先检查内存缓存
        session = self._assessments.get(assessment_id)
        if session:
            if self._is_expired(session):
                session.status = AssessmentStatus.EXPIRED
            return session
        
        # 从数据库恢复
        try:
            async with async_session() as db:
                stmt = select(Assessment).where(Assessment.id == int(assessment_id))
                result = await db.execute(stmt)
                db_assessment = result.scalar_one_or_none()
                
                if not db_assessment:
                    return None
                
                # 恢复会话对象
                session = AssessmentSession(
                    id=str(db_assessment.id),
                    user_id=str(db_assessment.user_id),
                    assessment_type=AssessmentType(db_assessment.assessment_type),
                    status=AssessmentStatus(db_assessment.status) if db_assessment.status in [s.value for s in AssessmentStatus] else AssessmentStatus.IN_PROGRESS,
                    current_question_index=0,
                    started_at=db_assessment.started_at,
                    completed_at=db_assessment.completed_at,
                    last_activity_at=db_assessment.updated_at or db_assessment.started_at,
                )
                
                # 从 responses 表恢复答案
                stmt = select(AssessmentResponse).where(AssessmentResponse.assessment_id == db_assessment.id)
                result = await db.execute(stmt)
                responses = result.scalars().all()
                
                for resp in responses:
                    # 找到对应的 strength_key
                    for q in VIA_QUESTIONS:
                        if q["id"] == int(resp.question_id):
                            session.answers[q["strength_key"]] = int(float(resp.response_score))
                            break
                
                # 更新进度
                session.current_question_index = len(session.answers)
                session.progress_percent = (len(session.answers) / len(VIA_QUESTIONS)) * 100
                
                # 缓存到内存
                self._assessments[assessment_id] = session
                
                if self._is_expired(session):
                    session.status = AssessmentStatus.EXPIRED
                
                return session
                
        except Exception as e:
            print(f"[AssessmentService] 从数据库恢复测评失败: {e}")
            return None
    
    async def get_questions(
        self, 
        assessment_id: str,
        from_index: Optional[int] = None,
        count: int = 1
    ) -> List[Dict[str, Any]]:
        """
        获取测评题目
        
        Args:
            assessment_id: 测评ID
            from_index: 起始题号（默认从当前进度开始）
            count: 获取题目数量
        
        Returns:
            题目列表
        """
        session = await self.get_assessment(assessment_id)
        if not session:
            return []
        
        if from_index is None:
            from_index = session.current_question_index
        
        # 获取题目
        questions = []
        for i in range(from_index, min(from_index + count, len(VIA_QUESTIONS))):
            q = VIA_QUESTIONS[i]
            questions.append({
                "id": q["id"],
                "question_number": q["question_number"],
                "text": q["text"],
                "category": q["category"],
                "strength": q["strength"],
                "strength_key": q["strength_key"],
                "description": q.get("description", ""),
            })
        
        return questions
    
    async def submit_answer(
        self, 
        assessment_id: str,
        question_id: int,
        score: int
    ) -> Dict[str, Any]:
        """
        提交答案
        
        Args:
            assessment_id: 测评ID
            question_id: 题目ID
            score: 得分 1-5
        
        Returns:
            提交结果，包含进度信息
        """
        session = await self.get_assessment(assessment_id)
        if not session:
            raise ValueError(f"测评不存在: {assessment_id}")
        
        if session.status == AssessmentStatus.COMPLETED:
            raise ValueError("测评已完成，不能继续答题")
        
        if session.status == AssessmentStatus.EXPIRED:
            raise ValueError("测评已过期")
        
        # 验证题目
        question = None
        for q in VIA_QUESTIONS:
            if q["id"] == question_id:
                question = q
                break
        
        if not question:
            raise ValueError(f"题目不存在: {question_id}")
        
        # 验证得分范围
        if not 1 <= score <= 5:
            raise ValueError("得分必须在1-5之间")
        
        # 保存答案
        strength_key = question["strength_key"]
        session.answers[strength_key] = score
        
        # 更新进度
        session.current_question_index += 1
        session.progress_percent = (
            len(session.answers) / len(VIA_QUESTIONS) * 100
        )
        session.last_activity_at = datetime.now()
        
        # 保存答题记录到数据库
        try:
            async with async_session() as db:
                db_response = AssessmentResponse(
                    assessment_id=int(assessment_id),
                    question_id=str(question_id),
                    question_text=question["text"],
                    response_value=str(score),
                    response_score=float(score),
                    response_time_ms=0,
                )
                db.add(db_response)
                await db.commit()
        except Exception as e:
            print(f"[AssessmentService] 保存答题记录失败: {e}")
            # 不影响主流程
        
        # 检查是否完成
        is_completed = len(session.answers) >= len(VIA_QUESTIONS)
        
        result = {
            "assessment_id": assessment_id,
            "current_question": session.current_question_index,
            "total_questions": len(VIA_QUESTIONS),
            "progress_percent": round(session.progress_percent, 1),
            "is_completed": is_completed,
        }
        
        # 如果完成，返回结果链接
        if is_completed:
            result["result_url"] = f"/api/v1/assessments/{assessment_id}/result"
        else:
            # 返回下一题
            next_questions = await self.get_questions(assessment_id, count=1)
            if next_questions:
                result["next_question"] = next_questions[0]
        
        return result
    
    async def submit_batch_answers(
        self,
        assessment_id: str,
        answers: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        批量提交答案
        
        Args:
            assessment_id: 测评ID
            answers: 答案列表 [{"question_id": 1, "score": 5}, ...]
        
        Returns:
            提交结果
        """
        session = await self.get_assessment(assessment_id)
        if not session:
            raise ValueError(f"测评不存在: {assessment_id}")
        
        for answer in answers:
            await self.submit_answer(
                assessment_id,
                answer["question_id"],
                answer["score"]
            )
        
        return {
            "assessment_id": assessment_id,
            "submitted_count": len(answers),
            "current_question": session.current_question_index,
            "total_questions": len(VIA_QUESTIONS),
            "progress_percent": round(session.progress_percent, 1),
            "is_completed": len(session.answers) >= len(VIA_QUESTIONS),
        }
    
    async def complete_assessment(
        self, 
        assessment_id: str
    ) -> AssessmentResult:
        """
        完成测评并计算结果
        
        Args:
            assessment_id: 测评ID
        
        Returns:
            测评结果
        """
        session = await self.get_assessment(assessment_id)
        if not session:
            raise ValueError(f"测评不存在: {assessment_id}")
        
        if len(session.answers) < len(VIA_QUESTIONS):
            raise ValueError("测评未完成，请先回答所有题目")
        
        # 计算耗时
        session.completed_at = datetime.now()
        if session.started_at:
            duration = session.completed_at - session.started_at
            session.duration_seconds = int(duration.total_seconds())
        
        # 计算结果
        result = self.scoring_engine.calculate_scores(
            responses=session.answers,
            assessment_id=assessment_id,
            user_id=session.user_id,
        )
        
        # 更新会话
        session.result = result
        session.status = AssessmentStatus.COMPLETED
        
        # 保存到数据库（关键修复）
        await self._save_to_database(session, result)
        
        return result
    
    async def _save_to_database(
        self,
        session: AssessmentSession,
        result: ScoringResult
    ) -> None:
        """
        将测评结果保存到数据库
        
        Args:
            session: 测评会话
            result: 测评结果
        """
        try:
            async with async_session() as db:
                # 1. 更新 Assessment 记录
                stmt = select(Assessment).where(Assessment.id == int(session.id))
                db_assessment = await db.execute(stmt)
                db_assessment = db_assessment.scalar_one_or_none()
                
                if db_assessment:
                    # 更新现有记录
                    db_assessment.status = DBAssessmentStatus.COMPLETED
                    db_assessment.score_summary = {
                        "balanced_score": result.balanced_score,
                        "top_strengths": [s.strength_key for s in result.top_strengths[:5]],
                        "dominant_virtue": result.dominant_virtue.virtue_code if result.dominant_virtue else None
                    }
                    db_assessment.interpretation = result.summary
                    db_assessment.recommendations = result.recommendations
                    db_assessment.completed_at = session.completed_at
                    db_assessment.title = f"VIA性格优势测评 - {session.completed_at.strftime('%Y-%m-%d')}" if session.completed_at else "VIA性格优势测评"
                    await db.flush()
                else:
                    print(f"[AssessmentService] 警告: Assessment {session.id} 不存在")
                    return
                
                # 2. 保存 AssessmentResult 详情（优势维度）
                for strength in result.top_strengths:
                    db_result = AssessmentResult(
                        assessment_id=db_assessment.id,
                        dimension_name=strength.strength_name,
                        dimension_code=strength.strength_key,
                        category=strength.virtue_category,
                        score=strength.raw_score,
                        normalized_score=strength.normalized_score,
                        percentile=strength.percentile,
                        rank=strength.rank,
                        interpretation=strength.description,
                        strengths_description=strength.description,
                        development_tips=f"发展建议: 继续发挥{strength.strength_name}优势",
                        related_strengths=[s.strength_key for s in result.top_strengths[:3] if s.strength_key != strength.strength_key]
                    )
                    db.add(db_result)
                
                # 3. 保存美德维度得分
                for virtue in result.virtue_scores:
                    db_result = AssessmentResult(
                        assessment_id=db_assessment.id,
                        dimension_name=virtue.virtue_name,
                        dimension_code=virtue.virtue_code,
                        category="VIRTUE",
                        score=virtue.average_score,
                        normalized_score=virtue.normalized_score,
                        percentile=virtue.percentile,
                        rank=virtue.rank,
                        interpretation=virtue.description,
                        strengths_description=f"包含{virtue.strengths_count}项优势",
                        related_strengths=[
                            s.strength_key for s in result.top_strengths 
                            if s.virtue_category == virtue.virtue_name
                        ]
                    )
                    db.add(db_result)
                
                await db.commit()
                print(f"[AssessmentService] 测评 {session.id} 结果已保存到数据库")
                
        except Exception as e:
            # 数据库保存失败不影响内存操作，但记录错误
            print(f"[AssessmentService] 保存到数据库失败: {e}")
            import traceback
            traceback.print_exc()
            # 不抛出异常，让流程继续
    
    async def get_result(
        self, 
        assessment_id: str
    ) -> Optional[ScoringResult]:
        """
        获取测评结果
        
        Args:
            assessment_id: 测评ID
        
        Returns:
            测评结果，如果不存在返回None
        """
        session = await self.get_assessment(assessment_id)
        if not session:
            return None
        
        # 如果答案已收集齐但还未完成，先完成测评
        if len(session.answers) >= len(VIA_QUESTIONS) and session.status != AssessmentStatus.COMPLETED:
            return await self.complete_assessment(assessment_id)
        
        # 如果已完成但未计算结果
        if session.status == AssessmentStatus.COMPLETED and not session.result:
            return await self.complete_assessment(assessment_id)
        
        return session.result
    
    async def get_progress(
        self, 
        assessment_id: str
    ) -> Optional[Dict[str, Any]]:
        """
        获取测评进度
        
        Args:
            assessment_id: 测评ID
        
        Returns:
            进度信息
        """
        session = await self.get_assessment(assessment_id)
        if not session:
            return None
        
        return {
            "assessment_id": assessment_id,
            "status": session.status.value,
            "progress_percent": round(session.progress_percent, 1),
            "answered_count": len(session.answers),
            "total_count": len(VIA_QUESTIONS),
            "current_question": session.current_question_index + 1,
            "last_activity_at": session.last_activity_at.isoformat() if session.last_activity_at else None,
        }
    
    async def get_user_assessments(
        self, 
        user_id: str,
        status: Optional[AssessmentStatus] = None,
        limit: int = 10,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """
        获取用户的测评历史（从数据库读取）
        
        Args:
            user_id: 用户ID
            status: 筛选状态（可选）
            limit: 返回数量限制
            offset: 偏移量
        
        Returns:
            测评历史列表
        """
        try:
            db_user_id = int(user_id) if user_id and user_id.isdigit() else 1
            
            async with async_session() as db:
                # 构建查询
                stmt = select(Assessment).where(Assessment.user_id == db_user_id)
                
                if status:
                    stmt = stmt.where(Assessment.status == status.value)
                
                # 按时间倒序排序
                stmt = stmt.order_by(Assessment.created_at.desc())
                
                # 分页
                stmt = stmt.offset(offset).limit(limit)
                
                result = await db.execute(stmt)
                db_assessments = result.scalars().all()
                
                # 转换为字典
                assessments = []
                for db_assessment in db_assessments:
                    data = {
                        "id": str(db_assessment.id),
                        "user_id": str(db_assessment.user_id),
                        "assessment_type": db_assessment.assessment_type,
                        "status": db_assessment.status,
                        "progress_percent": 100.0 if db_assessment.status == DBAssessmentStatus.COMPLETED else 0.0,
                        "answered_count": len(VIA_QUESTIONS) if db_assessment.status == DBAssessmentStatus.COMPLETED else 0,
                        "total_count": len(VIA_QUESTIONS),
                        "started_at": db_assessment.started_at.isoformat() if db_assessment.started_at else None,
                        "completed_at": db_assessment.completed_at.isoformat() if db_assessment.completed_at else None,
                        "duration_seconds": 0,
                    }
                    
                    # 添加结果摘要（如果已完成）
                    if db_assessment.status == DBAssessmentStatus.COMPLETED and db_assessment.score_summary:
                        top_strengths = db_assessment.score_summary.get("top_strengths", [])
                        data["result_summary"] = {
                            "top_strengths": [
                                {
                                    "rank": i + 1,
                                    "name": s,
                                    "score": 0,
                                    "percentile": 0,
                                }
                                for i, s in enumerate(top_strengths[:5])
                            ],
                            "dominant_virtue": db_assessment.score_summary.get("dominant_virtue", ""),
                        }
                    
                    assessments.append(data)
                
                return assessments
                
        except Exception as e:
            print(f"[AssessmentService] 从数据库获取测评历史失败: {e}")
            import traceback
            traceback.print_exc()
            # 降级到内存查询
            return await self._get_user_assessments_from_memory(user_id, status, limit, offset)
    
    async def _get_user_assessments_from_memory(
        self, 
        user_id: str,
        status: Optional[AssessmentStatus] = None,
        limit: int = 10,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """从内存获取测评历史（降级方案）"""
        assessments = []
        
        for session in self._assessments.values():
            if session.user_id != user_id:
                continue
            
            if status and session.status != status:
                continue
            
            assessments.append(self._session_to_dict(session))
        
        # 按时间倒序排序
        assessments.sort(
            key=lambda x: x.get("started_at", ""), 
            reverse=True
        )
        
        # 分页
        return assessments[offset:offset + limit]
    
    async def abandon_assessment(self, assessment_id: str) -> bool:
        """
        放弃测评（更新数据库）
        
        Args:
            assessment_id: 测评ID
        
        Returns:
            是否成功
        """
        session = await self.get_assessment(assessment_id)
        if not session:
            return False
        
        if session.status == AssessmentStatus.COMPLETED:
            return False
        
        session.status = AssessmentStatus.ABANDONED
        
        # 更新数据库
        try:
            async with async_session() as db:
                stmt = select(Assessment).where(Assessment.id == int(assessment_id))
                result = await db.execute(stmt)
                db_assessment = result.scalar_one_or_none()
                
                if db_assessment:
                    db_assessment.status = DBAssessmentStatus.ABANDONED
                    await db.commit()
        except Exception as e:
            print(f"[AssessmentService] 更新放弃状态失败: {e}")
        
        return True
    
    async def delete_assessment(self, assessment_id: str) -> bool:
        """
        删除测评（从数据库和内存中删除）
        
        Args:
            assessment_id: 测评ID
        
        Returns:
            是否成功
        """
        # 从内存删除
        if assessment_id in self._assessments:
            del self._assessments[assessment_id]
        
        # 从数据库删除
        try:
            async with async_session() as db:
                stmt = select(Assessment).where(Assessment.id == int(assessment_id))
                result = await db.execute(stmt)
                db_assessment = result.scalar_one_or_none()
                
                if db_assessment:
                    await db.delete(db_assessment)
                    await db.commit()
                    return True
        except Exception as e:
            print(f"[AssessmentService] 从数据库删除失败: {e}")
        
        return assessment_id not in self._assessments
    
    def _is_expired(self, session: AssessmentSession) -> bool:
        """
        检查测评是否过期
        
        Args:
            session: 测评会话
        
        Returns:
            是否过期
        """
        if session.status == AssessmentStatus.COMPLETED:
            return False
        
        if not session.last_activity_at:
            return False
        
        expiry_time = session.last_activity_at + timedelta(hours=self.EXPIRY_HOURS)
        return datetime.now() > expiry_time
    
    def _session_to_dict(self, session: AssessmentSession) -> Dict[str, Any]:
        """
        将会话转换为字典
        
        Args:
            session: 测评会话
        
        Returns:
            字典表示
        """
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
        
        # 添加结果摘要（如果已完成）
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
        
        return data
    
    async def get_assessment_config(
        self, 
        assessment_type: AssessmentType = AssessmentType.VIA_STRENGTHS
    ) -> Dict[str, Any]:
        """
        获取测评配置
        
        Args:
            assessment_type: 测评类型
        
        Returns:
            测评配置
        """
        return {
            "type": assessment_type.value,
            "config": ASSESSMENT_CONFIG,
            "total_questions": len(VIA_QUESTIONS),
            "estimated_time_minutes": ASSESSMENT_CONFIG["estimated_time_minutes"],
        }


# 全局测评服务实例
_assessment_service: Optional[AssessmentService] = None


def get_assessment_service() -> AssessmentService:
    """
    获取测评服务实例（单例模式）
    
    Returns:
        测评服务实例
    """
    global _assessment_service
    if _assessment_service is None:
        _assessment_service = AssessmentService()
    return _assessment_service
