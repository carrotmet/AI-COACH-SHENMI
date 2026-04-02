# -*- coding: utf-8 -*-
"""
报表生成服务模块

负责生成各类测评报表：
- 引流报表（简化版）
- 深度报表（完整版）
- 动态报表（趋势分析）
"""

import uuid
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from enum import Enum

from services.scoring_engine import AssessmentResult, get_scoring_engine
from services.assessment_service import AssessmentService, get_assessment_service
from data.report_templates import (
    QUICK_REPORT_TEMPLATE,
    FULL_REPORT_TEMPLATE,
    TREND_REPORT_TEMPLATE,
    get_report_template,
)
from data.strength_data import (
    get_strength_by_key,
    get_development_tips_by_level,
    VIRTUE_CATEGORIES,
)


class ReportType(str, Enum):
    """报表类型"""
    QUICK = "quick"  # 引流报表（免费版）
    FULL = "full"  # 深度报表（付费版）
    TREND = "trend"  # 动态报表（趋势分析）


class ReportStatus(str, Enum):
    """报表状态"""
    PENDING = "pending"  # 待生成
    GENERATING = "generating"  # 生成中
    COMPLETED = "completed"  # 已完成
    FAILED = "failed"  # 生成失败


@dataclass
class Report:
    """报表"""
    id: str
    user_id: Optional[str]
    assessment_id: str
    report_type: ReportType
    status: ReportStatus
    
    # 内容
    title: str
    content: Dict[str, Any] = field(default_factory=dict)
    
    # 文件
    pdf_url: Optional[str] = None
    image_url: Optional[str] = None
    
    # 时间
    created_at: datetime = field(default_factory=datetime.now)
    generated_at: Optional[datetime] = None
    expires_at: Optional[datetime] = None
    
    # 元数据
    is_premium: bool = False
    share_count: int = 0
    view_count: int = 0


class ReportService:
    """
    报表生成服务
    
    负责生成和管理各类测评报表
    """
    
    # 报表过期时间（天）
    REPORT_EXPIRY_DAYS = 30
    
    # 内存存储（实际项目中应使用数据库和文件存储）
    _reports: Dict[str, Report] = {}
    
    def __init__(self):
        """初始化报表服务"""
        self.assessment_service = get_assessment_service()
        self.scoring_engine = get_scoring_engine()
    
    async def generate_quick_report(
        self, 
        assessment_id: str,
        user_id: Optional[str] = None
    ) -> Report:
        """
        生成引流报表（简化版）
        
        Args:
            assessment_id: 测评ID
            user_id: 用户ID
        
        Returns:
            生成的报表
        """
        # 获取测评结果
        result = await self.assessment_service.get_result(assessment_id)
        if not result:
            raise ValueError(f"测评结果不存在: {assessment_id}")
        
        # 创建报表
        report_id = f"rpt_{uuid.uuid4().hex[:16]}"
        report = Report(
            id=report_id,
            user_id=user_id or result.user_id,
            assessment_id=assessment_id,
            report_type=ReportType.QUICK,
            status=ReportStatus.GENERATING,
            title="你的性格优势速览",
            is_premium=False,
        )
        
        # 生成内容
        content = self._build_quick_report_content(result)
        report.content = content
        report.status = ReportStatus.COMPLETED
        report.generated_at = datetime.now()
        report.expires_at = datetime.now() + timedelta(days=self.REPORT_EXPIRY_DAYS)
        
        # 保存报表
        self._reports[report_id] = report
        
        return report
    
    async def generate_full_report(
        self, 
        assessment_id: str,
        user_id: Optional[str] = None
    ) -> Report:
        """
        生成深度报表（完整版）
        
        Args:
            assessment_id: 测评ID
            user_id: 用户ID
        
        Returns:
            生成的报表
        """
        # 获取测评结果
        result = await self.assessment_service.get_result(assessment_id)
        if not result:
            raise ValueError(f"测评结果不存在: {assessment_id}")
        
        # 创建报表
        report_id = f"rpt_{uuid.uuid4().hex[:16]}"
        report = Report(
            id=report_id,
            user_id=user_id or result.user_id,
            assessment_id=assessment_id,
            report_type=ReportType.FULL,
            status=ReportStatus.GENERATING,
            title="完整性格优势分析报告",
            is_premium=True,
        )
        
        # 生成内容
        content = self._build_full_report_content(result)
        report.content = content
        report.status = ReportStatus.COMPLETED
        report.generated_at = datetime.now()
        report.expires_at = datetime.now() + timedelta(days=self.REPORT_EXPIRY_DAYS)
        
        # 保存报表
        self._reports[report_id] = report
        
        return report
    
    async def generate_trend_report(
        self, 
        user_id: str,
        assessment_ids: Optional[List[str]] = None,
        dimension: str = "strengths"
    ) -> Report:
        """
        生成动态报表（趋势分析）
        
        Args:
            user_id: 用户ID
            assessment_ids: 测评ID列表（可选，默认获取用户所有测评）
            dimension: 分析维度
        
        Returns:
            生成的报表
        """
        # 获取用户的测评历史
        if assessment_ids:
            assessments = []
            for aid in assessment_ids:
                result = await self.assessment_service.get_result(aid)
                if result:
                    assessments.append(result)
        else:
            # 获取用户最近的测评
            sessions = await self.assessment_service.get_user_assessments(
                user_id=user_id,
                status=None,
                limit=10,
            )
            assessments = []
            for session in sessions:
                if session.get("result_summary"):
                    result = await self.assessment_service.get_result(session["id"])
                    if result:
                        assessments.append(result)
        
        if len(assessments) < 2:
            raise ValueError("需要至少2次测评才能生成趋势报告")
        
        # 按时间排序
        assessments.sort(key=lambda x: x.completed_at)
        
        # 创建报表
        report_id = f"rpt_{uuid.uuid4().hex[:16]}"
        report = Report(
            id=report_id,
            user_id=user_id,
            assessment_id=assessments[-1].assessment_id,  # 使用最新的测评
            report_type=ReportType.TREND,
            status=ReportStatus.GENERATING,
            title="优势发展趋势报告",
            is_premium=True,
        )
        
        # 生成内容
        content = self._build_trend_report_content(assessments, dimension)
        report.content = content
        report.status = ReportStatus.COMPLETED
        report.generated_at = datetime.now()
        report.expires_at = datetime.now() + timedelta(days=self.REPORT_EXPIRY_DAYS)
        
        # 保存报表
        self._reports[report_id] = report
        
        return report
    
    async def get_report(self, report_id: str) -> Optional[Report]:
        """
        获取报表
        
        Args:
            report_id: 报表ID
        
        Returns:
            报表，如果不存在返回None
        """
        report = self._reports.get(report_id)
        if report:
            report.view_count += 1
        return report
    
    async def get_user_reports(
        self, 
        user_id: str,
        report_type: Optional[ReportType] = None,
        limit: int = 10,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """
        获取用户的报表列表
        
        Args:
            user_id: 用户ID
            report_type: 报表类型筛选
            limit: 返回数量限制
            offset: 偏移量
        
        Returns:
            报表列表
        """
        reports = []
        
        for report in self._reports.values():
            if report.user_id != user_id:
                continue
            
            if report_type and report.report_type != report_type:
                continue
            
            reports.append(self._report_to_dict(report))
        
        # 按时间倒序排序
        reports.sort(key=lambda x: x.get("created_at", ""), reverse=True)
        
        # 分页
        return reports[offset:offset + limit]
    
    async def delete_report(self, report_id: str) -> bool:
        """
        删除报表
        
        Args:
            report_id: 报表ID
        
        Returns:
            是否成功
        """
        if report_id in self._reports:
            del self._reports[report_id]
            return True
        return False
    
    def _build_quick_report_content(
        self, 
        result: AssessmentResult
    ) -> Dict[str, Any]:
        """
        构建引流报表内容
        
        Args:
            result: 测评结果
        
        Returns:
            报表内容
        """
        template = QUICK_REPORT_TEMPLATE
        
        # 构建核心优势部分
        top_strengths = []
        for i, strength in enumerate(result.top_strengths, 1):
            top_strengths.append({
                "rank": i,
                "name": strength.strength_name,
                "score": strength.raw_score,
                "percentile": strength.percentile,
                "description": strength.description,
                "icon": strength.icon,
                "color": strength.color,
            })
        
        # 构建美德领域概览
        virtue_summary = []
        for virtue in result.virtue_scores:
            virtue_summary.append({
                "code": virtue.virtue_code,
                "name": virtue.virtue_name,
                "score": round(virtue.average_score, 2),
                "percentile": virtue.percentile,
                "icon": virtue.icon,
                "color": virtue.color,
            })
        
        # 构建快速建议
        quick_tips = [
            f"在工作中寻找机会发挥你的{result.top_strengths[0].strength_name}，这会让你更有成就感",
            f"利用你的{result.top_strengths[1].strength_name}优势，尝试学习一项新技能",
            f"结合你的{result.top_strengths[2].strength_name}，设定一个本周可以实现的小目标",
        ]
        
        # 构建分享文本
        top_names = "、".join([s.strength_name for s in result.top_strengths[:3]])
        
        content = {
            "template": template["template_code"],
            "generated_at": datetime.now().isoformat(),
            "sections": {
                "cover": {
                    "title": template["content"]["cover"]["title"],
                    "subtitle": template["content"]["cover"]["subtitle"],
                    "description": template["content"]["cover"]["description"],
                },
                "top_strengths": {
                    "title": template["content"]["top_strengths"]["title"],
                    "subtitle": template["content"]["top_strengths"]["subtitle"],
                    "strengths": top_strengths,
                },
                "virtue_summary": {
                    "title": template["content"]["virtue_summary"]["title"],
                    "subtitle": template["content"]["virtue_summary"]["subtitle"],
                    "virtues": virtue_summary,
                    "chart_type": template["content"]["virtue_summary"]["chart_type"],
                },
                "quick_tips": {
                    "title": template["content"]["quick_tips"]["title"],
                    "subtitle": template["content"]["quick_tips"]["subtitle"],
                    "tips": quick_tips,
                },
                "cta": template["content"]["cta"],
            },
            "visual": template["visual"],
            "sharing": {
                **template["sharing"],
                "share_description": template["sharing"]["share_description"].format(
                    top_strengths=top_names
                ),
            },
            "summary": result.summary,
        }
        
        return content
    
    def _build_full_report_content(
        self, 
        result: AssessmentResult
    ) -> Dict[str, Any]:
        """
        构建深度报表内容
        
        Args:
            result: 测评结果
        
        Returns:
            报表内容
        """
        template = FULL_REPORT_TEMPLATE
        
        # 构建执行摘要
        executive_summary = {
            "profile_overview": {
                "dominant_virtue": result.dominant_virtue.virtue_name,
                "virtue_description": result.dominant_virtue.description,
                "balance_score": result.balanced_score,
            },
            "key_insights": [
                f"你的最强优势是{result.top_strengths[0].strength_name}，这让你在相关领域具有天然优势",
                f"你的前5大优势集中在{result.dominant_virtue.virtue_name}领域，形成了独特的优势组合",
                f"你的优势模式适合发挥{result.dominant_virtue.virtue_name}相关的工作和发展方向",
            ],
        }
        
        # 构建核心优势详解
        top_strengths_detail = []
        for strength in result.top_strengths:
            strength_def = get_strength_by_key(strength.strength_key)
            level = self._get_score_level(strength.percentile)
            
            top_strengths_detail.append({
                "rank": strength.rank,
                "name": strength.strength_name,
                "score": strength.raw_score,
                "normalized_score": strength.normalized_score,
                "percentile": strength.percentile,
                "level": level,
                "definition": strength.description,
                "characteristics": strength_def.get("characteristics", [])[:3] if strength_def else [],
                "applications": strength_def.get("applications", [])[:3] if strength_def else [],
                "development_tips": strength_def.get("development_tips", [])[:3] if strength_def else [],
                "icon": strength.icon,
                "color": strength.color,
            })
        
        # 构建完整优势排序
        all_strengths_ranking = []
        for strength in result.strength_scores:
            level = self._get_score_level(strength.percentile)
            all_strengths_ranking.append({
                "rank": strength.rank,
                "name": strength.strength_name,
                "virtue_category": strength.virtue_category,
                "score": strength.raw_score,
                "percentile": strength.percentile,
                "level": level,
                "icon": strength.icon,
                "color": strength.color,
            })
        
        # 构建美德领域分析
        virtue_analysis = []
        for virtue in result.virtue_scores:
            virtue_analysis.append({
                "code": virtue.virtue_code,
                "name": virtue.virtue_name,
                "average_score": round(virtue.average_score, 2),
                "normalized_score": virtue.normalized_score,
                "percentile": virtue.percentile,
                "rank": virtue.rank,
                "strengths_count": virtue.strengths_count,
                "strengths": [
                    {
                        "name": s.strength_name,
                        "score": s.raw_score,
                    }
                    for s in virtue.strengths
                ],
                "description": virtue.description,
                "icon": virtue.icon,
                "color": virtue.color,
            })
        
        # 构建优势组合分析
        strength_combinations = self._analyze_strength_combinations(result.top_strengths)
        
        # 构建发展计划
        development_plan = self._build_development_plan(result)
        
        # 构建行动清单
        action_items = self._build_action_items(result)
        
        content = {
            "template": template["template_code"],
            "generated_at": datetime.now().isoformat(),
            "sections": {
                "executive_summary": executive_summary,
                "top_strengths_detail": {
                    "title": template["content"]["top_strengths_detail"]["title"],
                    "strengths": top_strengths_detail,
                },
                "all_strengths_ranking": {
                    "title": template["content"]["all_strengths_ranking"]["title"],
                    "strengths": all_strengths_ranking,
                },
                "virtue_analysis": {
                    "title": template["content"]["virtue_analysis"]["title"],
                    "virtues": virtue_analysis,
                },
                "strength_combinations": strength_combinations,
                "development_plan": development_plan,
                "action_items": action_items,
                "resources": template["content"]["resources"],
            },
            "visual": template["visual"],
            "export": template["export"],
            "summary": result.summary,
            "interpretation": result.interpretation,
            "recommendations": result.recommendations,
        }
        
        return content
    
    def _build_trend_report_content(
        self, 
        assessments: List[AssessmentResult],
        dimension: str
    ) -> Dict[str, Any]:
        """
        构建动态报表内容
        
        Args:
            assessments: 测评结果列表
            dimension: 分析维度
        
        Returns:
            报表内容
        """
        template = TREND_REPORT_TEMPLATE
        
        # 计算时间跨度
        first_date = assessments[0].completed_at
        last_date = assessments[-1].completed_at
        time_span_days = (last_date - first_date).days
        
        # 构建趋势数据
        strength_trends = []
        virtue_trends = []
        
        # 获取所有优势的趋势
        if dimension == "strengths":
            strength_keys = set()
            for assessment in assessments:
                for s in assessment.strength_scores:
                    strength_keys.add(s.strength_key)
            
            for key in strength_keys:
                trend_data = []
                for assessment in assessments:
                    for s in assessment.strength_scores:
                        if s.strength_key == key:
                            trend_data.append({
                                "date": assessment.completed_at.isoformat(),
                                "score": s.raw_score,
                                "percentile": s.percentile,
                            })
                            break
                
                if len(trend_data) >= 2:
                    # 计算变化
                    first_score = trend_data[0]["score"]
                    last_score = trend_data[-1]["score"]
                    change = round(last_score - first_score, 2)
                    
                    strength_def = get_strength_by_key(key)
                    strength_trends.append({
                        "strength_key": key,
                        "name": strength_def["name_zh"] if strength_def else key,
                        "trend_data": trend_data,
                        "change": change,
                        "trend_direction": "up" if change > 0 else "down" if change < 0 else "stable",
                    })
        
        # 获取美德领域趋势
        for virtue_code in ["wisdom", "courage", "humanity", "justice", "temperance", "transcendence"]:
            trend_data = []
            for assessment in assessments:
                for v in assessment.virtue_scores:
                    if v.virtue_code == virtue_code:
                        trend_data.append({
                            "date": assessment.completed_at.isoformat(),
                            "score": v.average_score,
                            "percentile": v.percentile,
                        })
                        break
            
            if len(trend_data) >= 2:
                first_score = trend_data[0]["score"]
                last_score = trend_data[-1]["score"]
                change = round(last_score - first_score, 2)
                
                virtue_def = VIRTUE_CATEGORIES.get(virtue_code)
                virtue_trends.append({
                    "virtue_code": virtue_code,
                    "name": virtue_def["name"] if virtue_def else virtue_code,
                    "trend_data": trend_data,
                    "change": change,
                    "trend_direction": "up" if change > 0 else "down" if change < 0 else "stable",
                })
        
        # 构建进步洞察
        progress_insights = []
        
        # 找出显著提升的优势
        improved_strengths = [s for s in strength_trends if s["change"] > 0.5]
        if improved_strengths:
            for s in improved_strengths[:2]:
                progress_insights.append({
                    "type": "improved_strengths",
                    "title": "显著提升的优势",
                    "content": f"你的{s['name']}在{time_span_days}天内提升了{s['change']:.2f}分",
                })
        
        # 找出稳定的核心优势
        latest = assessments[-1]
        consistent_strengths = [s for s in latest.top_strengths if s.rank <= 3]
        if consistent_strengths:
            names = "、".join([s.strength_name for s in consistent_strengths[:2]])
            progress_insights.append({
                "type": "consistent_strengths",
                "title": "稳定的核心优势",
                "content": f"你的{names}始终保持在高水平",
            })
        
        # 构建建议
        recommendations = []
        if strength_trends:
            best_trend = max(strength_trends, key=lambda x: x["change"])
            recommendations.append(f"继续保持{best_trend['name']}的发展势头")
        
        content = {
            "template": template["template_code"],
            "generated_at": datetime.now().isoformat(),
            "time_span": {
                "days": time_span_days,
                "assessment_count": len(assessments),
                "first_date": first_date.isoformat(),
                "last_date": last_date.isoformat(),
            },
            "sections": {
                "strength_trends": {
                    "title": template["content"]["strength_trends"]["title"],
                    "trends": strength_trends,
                },
                "virtue_trends": {
                    "title": template["content"]["virtue_trends"]["title"],
                    "trends": virtue_trends,
                },
                "progress_insights": {
                    "title": template["content"]["progress_insights"]["title"],
                    "insights": progress_insights,
                },
                "recommendations": {
                    "title": template["content"]["recommendations"]["title"],
                    "items": recommendations,
                },
            },
            "visual": template["visual"],
        }
        
        return content
    
    def _analyze_strength_combinations(
        self, 
        top_strengths: List[Any]
    ) -> Dict[str, Any]:
        """
        分析优势组合
        
        Args:
            top_strengths: 前5大优势
        
        Returns:
            组合分析结果
        """
        if len(top_strengths) < 3:
            return {}
        
        # 黄金三角
        golden_triangle = {
            "name": "黄金三角",
            "strengths": [
                top_strengths[0].strength_name,
                top_strengths[1].strength_name,
                top_strengths[2].strength_name,
            ],
            "description": f"你的{top_strengths[0].strength_name}、{top_strengths[1].strength_name}和{top_strengths[2].strength_name}形成了强大的优势组合",
        }
        
        # 互补优势
        complementary = {
            "name": "互补优势",
            "pairs": [
                {
                    "strengths": [top_strengths[0].strength_name, top_strengths[1].strength_name],
                    "description": "这两个优势相互补充，帮助你在复杂任务中取得更好表现",
                }
            ],
        }
        
        return {
            "golden_triangle": golden_triangle,
            "complementary": complementary,
        }
    
    def _build_development_plan(
        self, 
        result: AssessmentResult
    ) -> Dict[str, Any]:
        """
        构建发展计划
        
        Args:
            result: 测评结果
        
        Returns:
            发展计划
        """
        top = result.top_strengths[0]
        mid = result.strength_scores[len(result.strength_scores) // 2]
        bottom = result.bottom_strengths[-1]
        
        return {
            "leverage_top": {
                "title": "发挥核心优势",
                "timeframe": "立即开始",
                "target": f"最大化发挥你的{top.strength_name}优势",
                "actions": [
                    f"在工作中主动承担需要{top.strength_name}的任务",
                    "每周至少一次刻意使用这一优势",
                    "记录使用这一优势的成功案例",
                    "帮助他人发展这方面的能力",
                ],
            },
            "develop_mid": {
                "title": "培养潜力优势",
                "timeframe": "3个月内",
                "target": f"提升你的{mid.strength_name}到更高水平",
                "actions": [
                    "每天练习使用这一优势15分钟",
                    "寻找能够应用这一优势的场景",
                    "向在这一方面有优势的人学习",
                    "定期反思和评估进步",
                ],
            },
            "balance_profile": {
                "title": "平衡优势档案",
                "timeframe": "6个月内",
                "target": "建立更加平衡的优势组合",
                "actions": [
                    f"识别需要关注的{bottom.strength_name}",
                    "寻找能够弥补这一领域的合作伙伴",
                    "在必要时进行基础练习",
                    "不要过分关注不足，而是发挥核心优势",
                ],
            },
        }
    
    def _build_action_items(
        self, 
        result: AssessmentResult
    ) -> List[Dict[str, Any]]:
        """
        构建行动清单
        
        Args:
            result: 测评结果
        
        Returns:
            行动清单
        """
        top = result.top_strengths[0]
        second = result.top_strengths[1]
        
        return [
            {
                "week": 1,
                "theme": "发现优势",
                "actions": [
                    f"每天记录一次使用{top.strength_name}的经历",
                    "向3位朋友询问他们认为你的优势是什么",
                    "回顾过去一年的成就，找出背后的优势",
                ],
            },
            {
                "week": 2,
                "theme": "应用优势",
                "actions": [
                    f"在工作中找到一个发挥{top.strength_name}的机会",
                    f"用{second.strength_name}帮助一位朋友或同事",
                    f"尝试将{top.strength_name}应用到一个新领域",
                ],
            },
            {
                "week": 3,
                "theme": "深化优势",
                "actions": [
                    f"学习一个与{top.strength_name}相关的新技能",
                    "阅读一本关于发挥优势的书籍",
                    "与AI优势教练深入讨论你的优势发展",
                ],
            },
            {
                "week": 4,
                "theme": "分享优势",
                "actions": [
                    "与他人分享你的优势发现",
                    "帮助他人识别他们的优势",
                    "制定下一个月的优势发展计划",
                ],
            },
        ]
    
    def _get_score_level(self, percentile: int) -> str:
        """
        根据百分位数获取水平描述
        
        Args:
            percentile: 百分位数
        
        Returns:
            水平描述
        """
        if percentile >= 90:
            return "卓越"
        elif percentile >= 75:
            return "优秀"
        elif percentile >= 50:
            return "良好"
        elif percentile >= 25:
            return "中等"
        else:
            return "发展"
    
    def _report_to_dict(self, report: Report) -> Dict[str, Any]:
        """
        将报表转换为字典
        
        Args:
            report: 报表
        
        Returns:
            字典表示
        """
        return {
            "id": report.id,
            "user_id": report.user_id,
            "assessment_id": report.assessment_id,
            "report_type": report.report_type.value,
            "status": report.status.value,
            "title": report.title,
            "is_premium": report.is_premium,
            "pdf_url": report.pdf_url,
            "image_url": report.image_url,
            "created_at": report.created_at.isoformat(),
            "generated_at": report.generated_at.isoformat() if report.generated_at else None,
            "expires_at": report.expires_at.isoformat() if report.expires_at else None,
            "view_count": report.view_count,
            "share_count": report.share_count,
        }


# 全局报表服务实例
_report_service: Optional[ReportService] = None


def get_report_service() -> ReportService:
    """
    获取报表服务实例（单例模式）
    
    Returns:
        报表服务实例
    """
    global _report_service
    if _report_service is None:
        _report_service = ReportService()
    return _report_service
