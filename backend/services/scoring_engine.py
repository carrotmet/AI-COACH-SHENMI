# -*- coding: utf-8 -*-
"""
评分引擎模块

负责心理测评的评分计算和结果分析

功能：
- 计算各优势维度得分
- 生成优势排序
- 计算百分位数
- 生成解读文本
"""

import math
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime

from data.via_questions import VIA_QUESTIONS, VIRTUE_CATEGORY_LIST
from data.strength_data import (
    VIA_STRENGTHS, 
    VIRTUE_CATEGORIES,
    get_strength_by_key,
    get_development_tips_by_level,
)


@dataclass
class StrengthScore:
    """单项优势得分"""
    strength_key: str
    strength_name: str
    virtue_category: str
    virtue_code: str
    raw_score: float  # 原始得分 1-5
    normalized_score: float  # 标准化得分 0-100
    percentile: int  # 百分位数
    rank: int  # 排名
    description: str
    icon: str
    color: str


@dataclass
class VirtueScore:
    """美德领域得分"""
    virtue_code: str
    virtue_name: str
    average_score: float
    normalized_score: float
    percentile: int
    rank: int
    strengths_count: int
    strengths: List[StrengthScore]
    description: str
    icon: str
    color: str


@dataclass
class AssessmentResult:
    """测评结果"""
    assessment_id: str
    user_id: Optional[str]
    assessment_type: str
    completed_at: datetime
    
    # 得分数据
    strength_scores: List[StrengthScore]  # 24项优势得分
    virtue_scores: List[VirtueScore]  # 6大美德得分
    
    # 排序结果
    top_strengths: List[StrengthScore]  # 前5大优势
    bottom_strengths: List[StrengthScore]  # 后5项优势
    
    # 分析结果
    dominant_virtue: VirtueScore  # 主导美德
    balanced_score: float  # 平衡性得分
    
    # 解读文本
    summary: str  # 总体摘要
    interpretation: Dict[str, str]  # 各维度解读
    recommendations: List[str]  # 发展建议


class ScoringEngine:
    """
    VIA测评评分引擎
    
    负责计算测评得分、生成排名和解读
    """
    
    # 评分范围
    SCORE_MIN = 1
    SCORE_MAX = 5
    
    # 标准化范围
    NORMALIZED_MIN = 0
    NORMALIZED_MAX = 100
    
    # 参考数据：基于大量样本的平均分和标准差（模拟数据）
    REFERENCE_STATS = {
        # 各项优势的平均分和标准差
        "strengths": {
            "creativity": {"mean": 3.5, "std": 0.8},
            "curiosity": {"mean": 3.8, "std": 0.7},
            "judgment": {"mean": 3.6, "std": 0.7},
            "love_of_learning": {"mean": 3.7, "std": 0.8},
            "perspective": {"mean": 3.4, "std": 0.8},
            "bravery": {"mean": 3.3, "std": 0.9},
            "perseverance": {"mean": 3.6, "std": 0.8},
            "honesty": {"mean": 4.0, "std": 0.7},
            "zest": {"mean": 3.5, "std": 0.9},
            "love": {"mean": 3.8, "std": 0.8},
            "kindness": {"mean": 3.9, "std": 0.7},
            "social_intelligence": {"mean": 3.5, "std": 0.8},
            "teamwork": {"mean": 3.7, "std": 0.7},
            "fairness": {"mean": 4.0, "std": 0.7},
            "leadership": {"mean": 3.4, "std": 0.9},
            "forgiveness": {"mean": 3.6, "std": 0.9},
            "humility": {"mean": 3.5, "std": 0.8},
            "prudence": {"mean": 3.4, "std": 0.8},
            "self_regulation": {"mean": 3.3, "std": 0.9},
            "appreciation_of_beauty": {"mean": 3.7, "std": 0.8},
            "gratitude": {"mean": 3.8, "std": 0.8},
            "hope": {"mean": 3.6, "std": 0.8},
            "humor": {"mean": 3.5, "std": 0.9},
            "spirituality": {"mean": 3.2, "std": 1.0},
        },
        # 美德领域的平均分和标准差
        "virtues": {
            "wisdom": {"mean": 3.6, "std": 0.6},
            "courage": {"mean": 3.6, "std": 0.7},
            "humanity": {"mean": 3.7, "std": 0.6},
            "justice": {"mean": 3.7, "std": 0.6},
            "temperance": {"mean": 3.4, "std": 0.7},
            "transcendence": {"mean": 3.6, "std": 0.7},
        },
    }
    
    def __init__(self):
        """初始化评分引擎"""
        self.questions_map = {q["strength_key"]: q for q in VIA_QUESTIONS}
    
    def calculate_scores(
        self, 
        responses: Dict[str, int],
        assessment_id: str = "",
        user_id: Optional[str] = None
    ) -> AssessmentResult:
        """
        计算测评得分
        
        Args:
            responses: 答题记录 {strength_key: score}
            assessment_id: 测评ID
            user_id: 用户ID
        
        Returns:
            完整的测评结果
        """
        # 计算各项优势得分
        strength_scores = self._calculate_strength_scores(responses)
        
        # 计算美德领域得分
        virtue_scores = self._calculate_virtue_scores(strength_scores)
        
        # 排序
        strength_scores_sorted = sorted(
            strength_scores, 
            key=lambda x: x.raw_score, 
            reverse=True
        )
        virtue_scores_sorted = sorted(
            virtue_scores, 
            key=lambda x: x.average_score, 
            reverse=True
        )
        
        # 更新排名
        for i, score in enumerate(strength_scores_sorted):
            score.rank = i + 1
        for i, score in enumerate(virtue_scores_sorted):
            score.rank = i + 1
        
        # 获取前5和后5优势
        top_strengths = strength_scores_sorted[:5]
        bottom_strengths = strength_scores_sorted[-5:]
        
        # 主导美德
        dominant_virtue = virtue_scores_sorted[0]
        
        # 计算平衡性得分
        balanced_score = self._calculate_balance_score(virtue_scores)
        
        # 生成解读
        summary = self._generate_summary(top_strengths, dominant_virtue)
        interpretation = self._generate_interpretation(strength_scores, virtue_scores)
        recommendations = self._generate_recommendations(top_strengths, bottom_strengths)
        
        return AssessmentResult(
            assessment_id=assessment_id,
            user_id=user_id,
            assessment_type="via_strengths",
            completed_at=datetime.now(),
            strength_scores=strength_scores_sorted,
            virtue_scores=virtue_scores_sorted,
            top_strengths=top_strengths,
            bottom_strengths=bottom_strengths,
            dominant_virtue=dominant_virtue,
            balanced_score=balanced_score,
            summary=summary,
            interpretation=interpretation,
            recommendations=recommendations,
        )
    
    def _calculate_strength_scores(
        self, 
        responses: Dict[str, int]
    ) -> List[StrengthScore]:
        """
        计算各项优势得分
        
        Args:
            responses: 答题记录
        
        Returns:
            各项优势得分列表
        """
        scores = []
        
        for strength_key, raw_score in responses.items():
            # 获取优势定义
            strength_def = get_strength_by_key(strength_key)
            question_def = self.questions_map.get(strength_key)
            
            if not strength_def or not question_def:
                continue
            
            # 标准化得分 (1-5 -> 0-100)
            normalized_score = self._normalize_score(raw_score)
            
            # 计算百分位数
            percentile = self._calculate_percentile(
                strength_key, 
                raw_score, 
                "strength"
            )
            
            score = StrengthScore(
                strength_key=strength_key,
                strength_name=strength_def["name_zh"],
                virtue_category=strength_def["virtue_category"],
                virtue_code=strength_def["virtue_code"],
                raw_score=raw_score,
                normalized_score=normalized_score,
                percentile=percentile,
                rank=0,  # 稍后更新
                description=strength_def["definition"],
                icon=strength_def.get("icon", "⭐"),
                color=strength_def.get("color", "#6366F1"),
            )
            scores.append(score)
        
        return scores
    
    def _calculate_virtue_scores(
        self, 
        strength_scores: List[StrengthScore]
    ) -> List[VirtueScore]:
        """
        计算美德领域得分
        
        Args:
            strength_scores: 各项优势得分
        
        Returns:
            美德领域得分列表
        """
        virtue_scores = []
        
        # 按美德分组
        virtue_groups: Dict[str, List[StrengthScore]] = {}
        for score in strength_scores:
            if score.virtue_code not in virtue_groups:
                virtue_groups[score.virtue_code] = []
            virtue_groups[score.virtue_code].append(score)
        
        # 计算每个美德的得分
        for virtue_code, scores in virtue_groups.items():
            virtue_def = VIRTUE_CATEGORIES.get(virtue_code)
            if not virtue_def:
                continue
            
            # 计算平均分
            avg_score = sum(s.raw_score for s in scores) / len(scores)
            normalized_score = self._normalize_score(avg_score)
            
            # 计算百分位数
            percentile = self._calculate_percentile(
                virtue_code, 
                avg_score, 
                "virtue"
            )
            
            virtue_score = VirtueScore(
                virtue_code=virtue_code,
                virtue_name=virtue_def["name"],
                average_score=avg_score,
                normalized_score=normalized_score,
                percentile=percentile,
                rank=0,  # 稍后更新
                strengths_count=len(scores),
                strengths=scores,
                description=virtue_def["description"],
                icon=virtue_def.get("icon", "⭐"),
                color=virtue_def.get("color", "#6366F1"),
            )
            virtue_scores.append(virtue_score)
        
        return virtue_scores
    
    def _normalize_score(self, raw_score: float) -> float:
        """
        将原始得分标准化到0-100范围
        
        Args:
            raw_score: 原始得分 1-5
        
        Returns:
            标准化得分 0-100
        """
        return ((raw_score - self.SCORE_MIN) / 
                (self.SCORE_MAX - self.SCORE_MIN)) * 100
    
    def _calculate_percentile(
        self, 
        key: str, 
        score: float, 
        score_type: str = "strength"
    ) -> int:
        """
        计算百分位数
        
        使用正态分布近似计算
        
        Args:
            key: 优势或美德代码
            score: 得分
            score_type: 类型 (strength/virtue)
        
        Returns:
            百分位数 0-100
        """
        # 获取参考统计数据
        if score_type == "strength":
            stats = self.REFERENCE_STATS["strengths"].get(key)
        else:
            stats = self.REFERENCE_STATS["virtues"].get(key)
        
        if not stats:
            # 使用默认统计
            mean = 3.5
            std = 0.8
        else:
            mean = stats["mean"]
            std = stats["std"]
        
        # 计算z-score
        if std == 0:
            return 50
        
        z_score = (score - mean) / std
        
        # 使用误差函数近似计算百分位数
        percentile = int(50 * (1 + math.erf(z_score / math.sqrt(2))))
        
        # 限制在0-100范围内
        return max(0, min(100, percentile))
    
    def _calculate_balance_score(
        self, 
        virtue_scores: List[VirtueScore]
    ) -> float:
        """
        计算优势档案的平衡性得分
        
        使用标准差的倒数来衡量平衡性
        
        Args:
            virtue_scores: 美德领域得分
        
        Returns:
            平衡性得分 0-100
        """
        if len(virtue_scores) < 2:
            return 100.0
        
        scores = [v.average_score for v in virtue_scores]
        mean = sum(scores) / len(scores)
        
        # 计算标准差
        variance = sum((s - mean) ** 2 for s in scores) / len(scores)
        std = math.sqrt(variance)
        
        # 标准差越小越平衡，转换为0-100分
        # 假设标准差范围0-1.5
        max_std = 1.5
        balance_score = max(0, 100 - (std / max_std) * 100)
        
        return round(balance_score, 1)
    
    def _generate_summary(
        self, 
        top_strengths: List[StrengthScore],
        dominant_virtue: VirtueScore
    ) -> str:
        """
        生成总体摘要
        
        Args:
            top_strengths: 前5大优势
            dominant_virtue: 主导美德
        
        Returns:
            摘要文本
        """
        top_names = "、".join([s.strength_name for s in top_strengths[:3]])
        
        summary = (
            f"根据VIA性格优势评估，你的核心优势是{top_names}。"
            f"你在{dominant_virtue.virtue_name}方面表现最为突出，"
            f"这反映了你对{dominant_virtue.description[:20]}...的重视。"
            f"这些优势是你在工作和生活中取得成功的重要资源，"
            f"建议你在日常中更多地发挥它们。"
        )
        
        return summary
    
    def _generate_interpretation(
        self,
        strength_scores: List[StrengthScore],
        virtue_scores: List[VirtueScore]
    ) -> Dict[str, str]:
        """
        生成各维度解读
        
        Args:
            strength_scores: 各项优势得分
            virtue_scores: 美德领域得分
        
        Returns:
            各维度解读文本
        """
        interpretation = {}
        
        # 解读主导美德
        dominant = virtue_scores[0]
        interpretation["dominant_virtue"] = (
            f"你的主导美德是{dominant.virtue_name}，"
            f"这表明你在{dominant.description[:30]}...方面有天然的优势。"
        )
        
        # 解读前3大优势
        for i, strength in enumerate(strength_scores[:3]):
            level = self._get_score_level(strength.percentile)
            interpretation[f"top_{i+1}"] = (
                f"你的{strength.strength_name}得分处于{strength.percentile}百分位，"
                f"属于{level}水平。{strength.description}"
            )
        
        # 解读平衡性
        balance_score = self._calculate_balance_score(virtue_scores)
        if balance_score >= 80:
            balance_desc = "非常平衡"
        elif balance_score >= 60:
            balance_desc = "比较平衡"
        elif balance_score >= 40:
            balance_desc = "一般平衡"
        else:
            balance_desc = "不太平衡"
        
        interpretation["balance"] = (
            f"你的优势档案{balance_desc}（平衡性得分：{balance_score}），"
            f"{'各美德领域发展较为均衡' if balance_score >= 60 else '某些领域可能需要更多关注'}。"
        )
        
        return interpretation
    
    def _generate_recommendations(
        self,
        top_strengths: List[StrengthScore],
        bottom_strengths: List[StrengthScore]
    ) -> List[str]:
        """
        生成发展建议
        
        Args:
            top_strengths: 前5大优势
            bottom_strengths: 后5项优势
        
        Returns:
            发展建议列表
        """
        recommendations = []
        
        # 针对核心优势的建议
        top_1 = top_strengths[0]
        recommendations.append(
            f"发挥你的{top_1.strength_name}优势："
            f"在工作中主动承担需要这一优势的任务，"
            f"这会让你更有成就感和满足感。"
        )
        
        # 针对前3优势的组合建议
        if len(top_strengths) >= 3:
            top_3_names = "、".join([s.strength_name for s in top_strengths[:3]])
            recommendations.append(
                f"利用你的优势组合（{top_3_names}）："
                f"这三个优势相互配合，可以帮助你在复杂任务中取得出色表现。"
            )
        
        # 针对发展空间的建议
        bottom_1 = bottom_strengths[0]
        recommendations.append(
            f"关注你的{bottom_1.strength_name}："
            f"这不是你的自然优势，但可以通过刻意练习来改善。"
            f"建议寻找能够弥补这一弱点的合作伙伴。"
        )
        
        # 通用建议
        recommendations.append(
            "持续使用优势日记：每天记录一次你使用核心优势的经历，"
            "这有助于你更好地认识和发挥这些优势。"
        )
        
        return recommendations
    
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
    
    def get_strength_level(self, score: float) -> str:
        """
        根据得分获取优势水平
        
        Args:
            score: 原始得分 1-5
        
        Returns:
            水平等级 (high/medium/low)
        """
        if score >= 4.0:
            return "high"
        elif score >= 3.0:
            return "medium"
        else:
            return "low"
    
    def generate_ranking(
        self, 
        strength_scores: List[StrengthScore]
    ) -> List[Dict[str, Any]]:
        """
        生成优势排名列表
        
        Args:
            strength_scores: 各项优势得分
        
        Returns:
            排名列表
        """
        sorted_scores = sorted(
            strength_scores, 
            key=lambda x: x.raw_score, 
            reverse=True
        )
        
        ranking = []
        for i, score in enumerate(sorted_scores, 1):
            ranking.append({
                "rank": i,
                "strength_key": score.strength_key,
                "strength_name": score.strength_name,
                "virtue_category": score.virtue_category,
                "raw_score": score.raw_score,
                "normalized_score": score.normalized_score,
                "percentile": score.percentile,
                "level": self.get_strength_level(score.raw_score),
                "icon": score.icon,
                "color": score.color,
            })
        
        return ranking
    
    def get_percentile(
        self, 
        score: float, 
        dimension: str, 
        dimension_type: str = "strength"
    ) -> int:
        """
        获取指定维度的百分位数
        
        Args:
            score: 得分
            dimension: 维度代码
            dimension_type: 维度类型
        
        Returns:
            百分位数
        """
        return self._calculate_percentile(dimension, score, dimension_type)


# 全局评分引擎实例
scoring_engine = ScoringEngine()


def get_scoring_engine() -> ScoringEngine:
    """
    获取评分引擎实例
    
    Returns:
        评分引擎实例
    """
    return scoring_engine
