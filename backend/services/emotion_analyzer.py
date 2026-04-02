# -*- coding: utf-8 -*-
"""
深觅 AI Coach - 情感分析服务

本模块提供用户消息的情感分析功能：
- 分析用户消息情感
- 识别情绪标签
- 情感强度评分
- 提供情感回应建议

支持两种分析方式：
1. 基于规则的关键词匹配（快速、轻量）
2. 基于LLM的深度学习分析（准确、智能）
"""

import re
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from enum import Enum
import logging

# 配置日志
logger = logging.getLogger(__name__)


class EmotionType(str, Enum):
    """情感类型枚举"""
    POSITIVE = "positive"                # 积极
    NEGATIVE = "negative"                # 消极
    ANXIOUS = "anxious"                  # 焦虑
    CONFUSED = "confused"                # 困惑
    FRUSTRATED = "frustrated"            # 沮丧
    EXCITED = "excited"                  # 兴奋
    GRATEFUL = "grateful"                # 感恩
    SAD = "sad"                          # 悲伤
    ANGRY = "angry"                      # 愤怒
    HOPEFUL = "hopeful"                  # 充满希望
    WORRIED = "worried"                  # 担忧
    NEUTRAL = "neutral"                  # 中性


class SentimentType(str, Enum):
    """情感倾向枚举"""
    POSITIVE = "positive"                # 积极
    NEGATIVE = "negative"                # 消极
    NEUTRAL = "neutral"                  # 中性
    MIXED = "mixed"                      # 混合


@dataclass
class EmotionAnalysisResult:
    """情感分析结果数据类"""
    emotion: EmotionType                 # 主要情感类型
    emotion_label: str                   # 情感标签（中文）
    sentiment: SentimentType             # 情感倾向
    intensity: float                     # 情感强度 (0-10)
    confidence: float                    # 置信度 (0-1)
    keywords: List[str]                  # 关键词
    explanation: str                     # 解释说明
    suggestions: List[str]               # 回应建议
    secondary_emotions: List[Dict[str, Any]] = field(default_factory=list)  # 次要情感

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "emotion": self.emotion.value,
            "emotion_label": self.emotion_label,
            "sentiment": self.sentiment.value,
            "intensity": self.intensity,
            "confidence": self.confidence,
            "keywords": self.keywords,
            "explanation": self.explanation,
            "suggestions": self.suggestions,
            "secondary_emotions": self.secondary_emotions
        }


# =============================================================================
# 情感关键词词典
# =============================================================================

EMOTION_KEYWORDS: Dict[EmotionType, List[str]] = {
    EmotionType.POSITIVE: [
        "开心", "高兴", "快乐", "愉快", "满足", "幸福", "棒", "好", "不错", "满意",
        "喜欢", "爱", "享受", "舒服", "轻松", "自在", "顺利", "成功", "成就",
        "自豪", "骄傲", "欣慰", "感激", "感谢", "赞美", "优秀", "完美", "精彩"
    ],
    EmotionType.NEGATIVE: [
        "难过", "伤心", "痛苦", "糟糕", "差", "不好", "失望", "绝望", "无助",
        "失败", "挫折", "困难", "问题", "麻烦", "担心", "害怕", "恐惧", "紧张",
        "压力", "累", "疲惫", "厌倦", "无聊", "空虚", "迷茫", "困惑"
    ],
    EmotionType.ANXIOUS: [
        "焦虑", "着急", "紧张", "不安", "忐忑", "心慌", "烦躁", "坐立不安",
        "睡不着", "失眠", "担心", "忧虑", "发愁", "纠结", "犹豫", "不确定",
        "害怕", "恐惧", "恐慌", "心惊", "紧张兮兮", "神经质"
    ],
    EmotionType.CONFUSED: [
        "困惑", "迷茫", "不清楚", "不明白", "不懂", "不知道", "疑惑", "疑问",
        "纠结", "犹豫", "难以抉择", "不确定", "模糊", "混乱", "复杂", "难解",
        "想不通", "理不清", "找不到方向", "迷失", "彷徨"
    ],
    EmotionType.FRUSTRATED: [
        "沮丧", "挫败", "失落", "气馁", "灰心", "失望", "绝望", "无力",
        "无奈", "郁闷", "压抑", "憋屈", "受打击", "失败", "不行", "做不到",
        "放弃", "算了", "没希望", "白费劲", "徒劳"
    ],
    EmotionType.EXCITED: [
        "兴奋", "激动", "振奋", "热血沸腾", "期待", "憧憬", "向往", "渴望",
        "迫不及待", "跃跃欲试", "充满干劲", "斗志昂扬", "激情", "热烈", "狂热",
        "开心极了", "太棒了", "太好了", "惊喜", "惊讶"
    ],
    EmotionType.GRATEFUL: [
        "感谢", "感激", "感恩", "谢谢", "多谢", "铭记", "难忘", "感动",
        "温暖", "贴心", "关怀", "支持", "帮助", "陪伴", "理解", "包容",
        "珍惜", "珍视", "重视", "尊重"
    ],
    EmotionType.SAD: [
        "悲伤", "难过", "伤心", "痛苦", "哭泣", "流泪", "心碎", "心痛",
        "失落", "空虚", "孤独", "寂寞", "想念", "怀念", "遗憾", "后悔",
        "自责", "内疚", "惭愧", "对不起"
    ],
    EmotionType.ANGRY: [
        "生气", "愤怒", "恼火", "气愤", "火大", "不爽", "讨厌", "恨",
        "烦", "烦躁", "暴躁", "暴怒", "忍无可忍", "受够了", "不满", "抱怨",
        "指责", "批评", "攻击", "冲突"
    ],
    EmotionType.HOPEFUL: [
        "希望", "期待", "憧憬", "向往", "相信", "信任", "乐观", "积极",
        "向上", "进取", "努力", "奋斗", "坚持", "毅力", "决心", "信心",
        "自信", "勇敢", "无畏", "大胆"
    ],
    EmotionType.WORRIED: [
        "担心", "担忧", "忧虑", "发愁", "苦恼", "困扰", "烦恼", "焦虑",
        "紧张", "不安", "忐忑", "悬着", "放不下", "牵挂", "惦记", "操心",
        "费心", "劳神", "伤脑筋", "为难"
    ]
}

# 情感强度修饰词
INTENSITY_MODIFIERS = {
    "high": ["非常", "特别", "极其", "超级", "十分", "很", "太", "巨", "无比", "极端", "强烈", "深度"],
    "medium": ["比较", "挺", "有点", "有些", "稍微", "略", "还算", "一般"],
    "low": ["有点", "略微", "稍稍", "一丝", "一点", "轻微", "不太", "不怎么"]
}

# 否定词
NEGATION_WORDS = ["不", "没", "无", "非", "莫", "勿", "未", "别", "没有", "不是", "不能", "不会"]


# =============================================================================
# 情感分析器
# =============================================================================

class EmotionAnalyzer:
    """情感分析器
    
    提供基于规则和LLM的情感分析功能
    """
    
    def __init__(self, use_llm: bool = False):
        """初始化情感分析器
        
        Args:
            use_llm: 是否使用LLM进行深度分析
        """
        self.use_llm = use_llm
        self._llm_service = None
        
        if use_llm:
            try:
                from services.llm_service import get_llm_service
                self._llm_service = get_llm_service()
            except Exception as e:
                logger.warning(f"LLM服务初始化失败，将使用规则分析: {e}")
                self.use_llm = False
    
    async def analyze(
        self,
        text: str,
        use_llm: Optional[bool] = None
    ) -> EmotionAnalysisResult:
        """分析文本情感
        
        Args:
            text: 需要分析的文本
            use_llm: 是否使用LLM分析，None则使用初始化时的设置
            
        Returns:
            情感分析结果
        """
        # 优先使用参数指定的分析方式
        should_use_llm = use_llm if use_llm is not None else self.use_llm
        
        if should_use_llm and self._llm_service:
            try:
                return await self._analyze_with_llm(text)
            except Exception as e:
                logger.warning(f"LLM分析失败，降级到规则分析: {e}")
        
        return self._analyze_with_rules(text)
    
    def _analyze_with_rules(self, text: str) -> EmotionAnalysisResult:
        """基于规则的情感分析
        
        Args:
            text: 需要分析的文本
            
        Returns:
            情感分析结果
        """
        text_lower = text.lower()
        
        # 统计各情感类型的匹配次数
        emotion_scores: Dict[EmotionType, Tuple[int, List[str]]] = {}
        
        for emotion_type, keywords in EMOTION_KEYWORDS.items():
            matches = []
            score = 0
            
            for keyword in keywords:
                if keyword in text:
                    # 检查是否有否定词修饰
                    negation_count = self._count_negation_before(text, keyword)
                    if negation_count % 2 == 0:  # 偶数次否定=肯定
                        matches.append(keyword)
                        score += 1
                        # 检查强度修饰词
                        intensity = self._detect_intensity(text, keyword)
                        score += intensity * 0.5
            
            if matches:
                emotion_scores[emotion_type] = (score, matches)
        
        # 如果没有匹配到任何情感词，返回中性
        if not emotion_scores:
            return EmotionAnalysisResult(
                emotion=EmotionType.NEUTRAL,
                emotion_label="中性",
                sentiment=SentimentType.NEUTRAL,
                intensity=5.0,
                confidence=0.5,
                keywords=[],
                explanation="未检测到明显的情感信号",
                suggestions=["继续倾听和探索"]
            )
        
        # 找出得分最高的情感
        primary_emotion = max(emotion_scores.keys(), key=lambda e: emotion_scores[e][0])
        primary_score, primary_keywords = emotion_scores[primary_emotion]
        
        # 找出次要情感
        secondary_emotions = []
        for emotion, (score, keywords) in emotion_scores.items():
            if emotion != primary_emotion and score > 0:
                secondary_emotions.append({
                    "emotion": emotion.value,
                    "label": self._get_emotion_label(emotion),
                    "score": score
                })
        
        # 按得分排序
        secondary_emotions.sort(key=lambda x: x["score"], reverse=True)
        secondary_emotions = secondary_emotions[:2]  # 只保留前2个
        
        # 计算情感倾向
        sentiment = self._determine_sentiment(primary_emotion, secondary_emotions)
        
        # 计算情感强度
        intensity = self._calculate_intensity(text, primary_score)
        
        # 计算置信度
        confidence = min(0.5 + primary_score * 0.1, 0.95)
        
        # 生成解释
        explanation = self._generate_explanation(primary_emotion, primary_keywords)
        
        # 生成回应建议
        suggestions = self._generate_suggestions(primary_emotion, intensity)
        
        return EmotionAnalysisResult(
            emotion=primary_emotion,
            emotion_label=self._get_emotion_label(primary_emotion),
            sentiment=sentiment,
            intensity=intensity,
            confidence=confidence,
            keywords=primary_keywords[:5],
            explanation=explanation,
            suggestions=suggestions,
            secondary_emotions=secondary_emotions
        )
    
    async def _analyze_with_llm(self, text: str) -> EmotionAnalysisResult:
        """基于LLM的情感分析
        
        Args:
            text: 需要分析的文本
            
        Returns:
            情感分析结果
        """
        if not self._llm_service:
            raise ValueError("LLM服务未初始化")
        
        # 使用LLM服务进行情感分析
        result = await self._llm_service.analyze_sentiment(text)
        
        # 解析LLM返回的结果
        emotion_str = result.get("emotion", "neutral").lower()
        emotion = self._parse_emotion_type(emotion_str)
        
        return EmotionAnalysisResult(
            emotion=emotion,
            emotion_label=self._get_emotion_label(emotion),
            sentiment=self._parse_sentiment_type(result.get("sentiment", "neutral")),
            intensity=float(result.get("intensity", 5)),
            confidence=0.85,
            keywords=result.get("keywords", []),
            explanation=result.get("explanation", ""),
            suggestions=self._generate_suggestions(emotion, float(result.get("intensity", 5)))
        )
    
    def _count_negation_before(self, text: str, keyword: str) -> int:
        """计算关键词前的否定词数量
        
        Args:
            text: 文本
            keyword: 关键词
            
        Returns:
            否定词数量
        """
        # 找到关键词位置
        pos = text.find(keyword)
        if pos == -1:
            return 0
        
        # 获取关键词前的文本（最多20个字符）
        before_text = text[max(0, pos - 20):pos]
        
        # 统计否定词
        count = 0
        for neg_word in NEGATION_WORDS:
            count += before_text.count(neg_word)
        
        return count
    
    def _detect_intensity(self, text: str, keyword: str) -> float:
        """检测情感强度修饰词
        
        Args:
            text: 文本
            keyword: 关键词
            
        Returns:
            强度值 (0-2)
        """
        pos = text.find(keyword)
        if pos == -1:
            return 0.0
        
        # 获取关键词前后的文本
        context = text[max(0, pos - 10):min(len(text), pos + len(keyword) + 10)]
        
        # 检查高强度修饰词
        for modifier in INTENSITY_MODIFIERS["high"]:
            if modifier in context:
                return 2.0
        
        # 检查中强度修饰词
        for modifier in INTENSITY_MODIFIERS["medium"]:
            if modifier in context:
                return 1.0
        
        # 检查低强度修饰词
        for modifier in INTENSITY_MODIFIERS["low"]:
            if modifier in context:
                return 0.5
        
        return 0.0
    
    def _calculate_intensity(self, text: str, score: float) -> float:
        """计算情感强度
        
        Args:
            text: 文本
            score: 情感得分
            
        Returns:
            强度值 (0-10)
        """
        # 基础强度
        base_intensity = min(score * 2, 6)
        
        # 根据文本特征调整
        # 感叹号增加强度
        exclamation_count = text.count("！") + text.count("!")
        base_intensity += min(exclamation_count * 0.5, 2)
        
        # 重复标点增加强度
        if "。。。" in text or "..." in text:
            base_intensity -= 1  # 省略号可能表示犹豫或低落
        
        # 大写字母或重复字符
        if re.search(r'(.)\1{2,}', text):  # 重复字符
            base_intensity += 0.5
        
        return min(max(base_intensity, 1), 10)
    
    def _determine_sentiment(
        self,
        primary_emotion: EmotionType,
        secondary_emotions: List[Dict[str, Any]]
    ) -> SentimentType:
        """确定情感倾向
        
        Args:
            primary_emotion: 主要情感
            secondary_emotions: 次要情感
            
        Returns:
            情感倾向
        """
        positive_emotions = {
            EmotionType.POSITIVE, EmotionType.EXCITED,
            EmotionType.GRATEFUL, EmotionType.HOPEFUL
        }
        negative_emotions = {
            EmotionType.NEGATIVE, EmotionType.ANXIOUS,
            EmotionType.CONFUSED, EmotionType.FRUSTRATED,
            EmotionType.SAD, EmotionType.ANGRY, EmotionType.WORRIED
        }
        
        if primary_emotion in positive_emotions:
            return SentimentType.POSITIVE
        elif primary_emotion in negative_emotions:
            return SentimentType.NEGATIVE
        elif primary_emotion == EmotionType.NEUTRAL:
            return SentimentType.NEUTRAL
        else:
            return SentimentType.MIXED
    
    def _get_emotion_label(self, emotion: EmotionType) -> str:
        """获取情感类型的中文标签
        
        Args:
            emotion: 情感类型
            
        Returns:
            中文标签
        """
        labels = {
            EmotionType.POSITIVE: "积极",
            EmotionType.NEGATIVE: "消极",
            EmotionType.ANXIOUS: "焦虑",
            EmotionType.CONFUSED: "困惑",
            EmotionType.FRUSTRATED: "沮丧",
            EmotionType.EXCITED: "兴奋",
            EmotionType.GRATEFUL: "感恩",
            EmotionType.SAD: "悲伤",
            EmotionType.ANGRY: "愤怒",
            EmotionType.HOPEFUL: "充满希望",
            EmotionType.WORRIED: "担忧",
            EmotionType.NEUTRAL: "中性"
        }
        return labels.get(emotion, "未知")
    
    def _parse_emotion_type(self, emotion_str: str) -> EmotionType:
        """解析情感类型字符串
        
        Args:
            emotion_str: 情感类型字符串
            
        Returns:
            EmotionType
        """
        emotion_map = {
            "positive": EmotionType.POSITIVE,
            "negative": EmotionType.NEGATIVE,
            "anxious": EmotionType.ANXIOUS,
            "confused": EmotionType.CONFUSED,
            "frustrated": EmotionType.FRUSTRATED,
            "excited": EmotionType.EXCITED,
            "grateful": EmotionType.GRATEFUL,
            "sad": EmotionType.SAD,
            "angry": EmotionType.ANGRY,
            "hopeful": EmotionType.HOPEFUL,
            "worried": EmotionType.WORRIED,
            "neutral": EmotionType.NEUTRAL
        }
        return emotion_map.get(emotion_str.lower(), EmotionType.NEUTRAL)
    
    def _parse_sentiment_type(self, sentiment_str: str) -> SentimentType:
        """解析情感倾向字符串
        
        Args:
            sentiment_str: 情感倾向字符串
            
        Returns:
            SentimentType
        """
        sentiment_map = {
            "positive": SentimentType.POSITIVE,
            "negative": SentimentType.NEGATIVE,
            "neutral": SentimentType.NEUTRAL,
            "mixed": SentimentType.MIXED
        }
        return sentiment_map.get(sentiment_str.lower(), SentimentType.NEUTRAL)
    
    def _generate_explanation(self, emotion: EmotionType, keywords: List[str]) -> str:
        """生成情感解释
        
        Args:
            emotion: 情感类型
            keywords: 关键词
            
        Returns:
            解释文本
        """
        keyword_str = "、".join(keywords[:3]) if keywords else "相关表达"
        
        explanations = {
            EmotionType.POSITIVE: f"文本中出现了'{keyword_str}'等积极表达，表明用户处于积极正向的情绪状态",
            EmotionType.NEGATIVE: f"文本中出现了'{keyword_str}'等消极表达，用户可能正在经历一些困扰",
            EmotionType.ANXIOUS: f"文本中出现了'{keyword_str}'等焦虑表达，用户可能感到紧张或担忧",
            EmotionType.CONFUSED: f"文本中出现了'{keyword_str}'等困惑表达，用户可能面临选择困难或方向迷茫",
            EmotionType.FRUSTRATED: f"文本中出现了'{keyword_str}'等沮丧表达，用户可能遇到了挫折或困难",
            EmotionType.EXCITED: f"文本中出现了'{keyword_str}'等兴奋表达，用户对某事充满期待和热情",
            EmotionType.GRATEFUL: f"文本中出现了'{keyword_str}'等感恩表达，用户表达了感谢和认可",
            EmotionType.SAD: f"文本中出现了'{keyword_str}'等悲伤表达，用户可能正在经历失落或难过",
            EmotionType.ANGRY: f"文本中出现了'{keyword_str}'等愤怒表达，用户可能感到不满或受挫",
            EmotionType.HOPEFUL: f"文本中出现了'{keyword_str}'等希望表达，用户对未来持乐观态度",
            EmotionType.WORRIED: f"文本中出现了'{keyword_str}'等担忧表达，用户对某些事情放心不下",
            EmotionType.NEUTRAL: "文本中未检测到明显的情感倾向，情绪状态较为平稳"
        }
        
        return explanations.get(emotion, "情感状态待进一步分析")
    
    def _generate_suggestions(self, emotion: EmotionType, intensity: float) -> List[str]:
        """生成回应建议
        
        Args:
            emotion: 情感类型
            intensity: 情感强度
            
        Returns:
            建议列表
        """
        suggestions = {
            EmotionType.POSITIVE: [
                "真诚祝贺用户的积极体验",
                "帮助用户识别发挥的优势",
                "鼓励用户继续保持",
                "探索如何将这种体验延续"
            ],
            EmotionType.NEGATIVE: [
                "共情理解，接纳用户的情绪",
                "不急于提供解决方案",
                "倾听用户的完整故事",
                "帮助发现内在资源"
            ],
            EmotionType.ANXIOUS: [
                "帮助用户回到当下",
                "引导深呼吸或放松练习",
                "探索焦虑的具体来源",
                "区分可控与不可控因素"
            ],
            EmotionType.CONFUSED: [
                "正常化困惑情绪",
                "通过提问澄清困惑",
                "提供新的思考角度",
                "陪伴用户一起探索"
            ],
            EmotionType.FRUSTRATED: [
                "认可用户的努力",
                "帮助从挫折中学习",
                "重新定义失败的意义",
                "重建信心和动力"
            ],
            EmotionType.EXCITED: [
                "分享用户的热情",
                "探索兴奋背后的期待",
                "将兴奋转化为行动",
                "帮助制定实现计划"
            ],
            EmotionType.GRATEFUL: [
                "真诚接纳用户的感谢",
                "引导用户感恩自己",
                "强化积极互动",
                "培养感恩习惯"
            ],
            EmotionType.SAD: [
                "允许悲伤的存在",
                "表达陪伴和支持",
                "不急于让情绪变好",
                "给予情绪充分空间"
            ],
            EmotionType.ANGRY: [
                "接纳愤怒情绪",
                "了解愤怒的原因",
                "不评判用户的反应",
                "引导建设性表达"
            ],
            EmotionType.HOPEFUL: [
                "强化希望和信心",
                "帮助明确目标",
                "制定实现路径",
                "庆祝积极态度"
            ],
            EmotionType.WORRIED: [
                "理解担忧的来源",
                "区分合理担忧和过度担忧",
                "提供实际支持",
                "帮助放下不必要的担忧"
            ],
            EmotionType.NEUTRAL: [
                "继续倾听和探索",
                "通过提问了解深层状态",
                "保持开放和好奇",
                "等待情感信号的出现"
            ]
        }
        
        base_suggestions = suggestions.get(emotion, ["继续倾听和探索"])
        
        # 根据强度调整建议
        if intensity > 8:
            base_suggestions.insert(0, "优先处理强烈的情绪")
        elif intensity < 3:
            base_suggestions.append("关注是否有压抑的情绪")
        
        return base_suggestions[:4]
    
    def quick_analyze(self, text: str) -> Dict[str, Any]:
        """快速情感分析（同步版本）
        
        Args:
            text: 需要分析的文本
            
        Returns:
            简化的分析结果
        """
        result = self._analyze_with_rules(text)
        return {
            "emotion": result.emotion.value,
            "emotion_label": result.emotion_label,
            "sentiment": result.sentiment.value,
            "intensity": result.intensity,
            "keywords": result.keywords
        }


# =============================================================================
# 便捷函数和全局实例
# =============================================================================

# 全局情感分析器实例
_emotion_analyzer: Optional[EmotionAnalyzer] = None


def get_emotion_analyzer(use_llm: bool = False) -> EmotionAnalyzer:
    """获取全局情感分析器实例
    
    Args:
        use_llm: 是否使用LLM
        
    Returns:
        EmotionAnalyzer实例
    """
    global _emotion_analyzer
    if _emotion_analyzer is None:
        _emotion_analyzer = EmotionAnalyzer(use_llm=use_llm)
    return _emotion_analyzer


def init_emotion_analyzer(use_llm: bool = False) -> EmotionAnalyzer:
    """初始化情感分析器
    
    Args:
        use_llm: 是否使用LLM
        
    Returns:
        EmotionAnalyzer实例
    """
    global _emotion_analyzer
    _emotion_analyzer = EmotionAnalyzer(use_llm=use_llm)
    return _emotion_analyzer


async def analyze_emotion(text: str, use_llm: bool = False) -> EmotionAnalysisResult:
    """快速情感分析函数
    
    Args:
        text: 需要分析的文本
        use_llm: 是否使用LLM
        
    Returns:
        情感分析结果
    """
    analyzer = get_emotion_analyzer(use_llm=use_llm)
    return await analyzer.analyze(text, use_llm=use_llm)
