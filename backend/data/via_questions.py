# -*- coding: utf-8 -*-
"""
VIA品格优势评估题目数据（简化版24题）

每道题目对应一种性格优势，共覆盖VIA 24种性格优势
分为6大美德领域：智慧、勇气、人道、正义、节制、超越

评分标准：1-5分
1 = 非常不符合
2 = 不太符合
3 = 一般
4 = 比较符合
5 = 非常符合
"""

from typing import List, Dict, Any

# 选项配置
VIA_QUESTION_OPTIONS = [
    {"value": 1, "label": "非常不符合", "description": "这完全不像我"},
    {"value": 2, "label": "不太符合", "description": "这不太像我"},
    {"value": 3, "label": "一般", "description": "这有点像我"},
    {"value": 4, "label": "比较符合", "description": "这比较像我"},
    {"value": 5, "label": "非常符合", "description": "这正是我"},
]

# VIA 24题简化版测评题目
# 每题对应一种性格优势
VIA_QUESTIONS: List[Dict[str, Any]] = [
    # ========== 智慧与知识 (Wisdom & Knowledge) ==========
    {
        "id": 1,
        "question_number": 1,
        "text": "我喜欢学习和探索新知识，对世界充满好奇",
        "category": "智慧与知识",
        "category_code": "wisdom",
        "strength": "好奇心",
        "strength_key": "curiosity",
        "description": "对新事物、新体验保持开放和渴望了解的态度",
    },
    {
        "id": 2,
        "question_number": 2,
        "text": "我善于从不同角度思考问题，提出创新的解决方案",
        "category": "智慧与知识",
        "category_code": "wisdom",
        "strength": "创造力",
        "strength_key": "creativity",
        "description": "能够产生新颖且有价值的想法和解决方案",
    },
    {
        "id": 3,
        "question_number": 3,
        "text": "我在做决策时会仔细权衡各种证据和可能性",
        "category": "智慧与知识",
        "category_code": "wisdom",
        "strength": "判断力",
        "strength_key": "judgment",
        "description": "能够客观分析信息，做出明智的决策",
    },
    {
        "id": 4,
        "question_number": 4,
        "text": "我热爱学习新技能，享受掌握新知识的过程",
        "category": "智慧与知识",
        "category_code": "wisdom",
        "strength": "热爱学习",
        "strength_key": "love_of_learning",
        "description": "对获取新知识和技能有强烈的内在动机",
    },
    {
        "id": 5,
        "question_number": 5,
        "text": "朋友们经常来找我寻求建议，因为我能提供有价值的观点",
        "category": "智慧与知识",
        "category_code": "wisdom",
        "strength": "洞察力",
        "strength_key": "perspective",
        "description": "能够为他人提供明智的建议和深刻的见解",
    },
    
    # ========== 勇气 (Courage) ==========
    {
        "id": 6,
        "question_number": 6,
        "text": "即使面对困难和恐惧，我也能坚持自己的信念并采取行动",
        "category": "勇气",
        "category_code": "courage",
        "strength": "勇敢",
        "strength_key": "bravery",
        "description": "面对威胁、困难或痛苦时不退缩",
    },
    {
        "id": 7,
        "question_number": 7,
        "text": "我能够坚持不懈地追求目标，即使遇到挫折也不轻易放弃",
        "category": "勇气",
        "category_code": "courage",
        "strength": "毅力",
        "strength_key": "perseverance",
        "description": "能够坚持完成任务，克服障碍达成目标",
    },
    {
        "id": 8,
        "question_number": 8,
        "text": "我总是诚实地表达自己的想法，即使这可能会让我处于不利地位",
        "category": "勇气",
        "category_code": "courage",
        "strength": "诚实",
        "strength_key": "honesty",
        "description": "言行一致，真实表达自己的想法和感受",
    },
    {
        "id": 9,
        "question_number": 9,
        "text": "我对生活充满热情和活力，总是积极投入各种活动",
        "category": "勇气",
        "category_code": "courage",
        "strength": "热情",
        "strength_key": "zest",
        "description": "对生活充满能量和热情，积极投入",
    },
    
    # ========== 人道 (Humanity) ==========
    {
        "id": 10,
        "question_number": 10,
        "text": "我能够与他人建立亲密、温暖的关系，珍惜亲密关系",
        "category": "人道",
        "category_code": "humanity",
        "strength": "爱与被爱",
        "strength_key": "love",
        "description": "能够与他人建立亲密关系，珍视情感联结",
    },
    {
        "id": 11,
        "question_number": 11,
        "text": "我经常帮助他人，乐于为他人做好事而不求回报",
        "category": "人道",
        "category_code": "humanity",
        "strength": "善良",
        "strength_key": "kindness",
        "description": "乐于助人，关心他人的福祉",
    },
    {
        "id": 12,
        "question_number": 12,
        "text": "我善于理解他人的感受和动机，能够根据情况调整自己的行为",
        "category": "人道",
        "category_code": "humanity",
        "strength": "社交智慧",
        "strength_key": "social_intelligence",
        "description": "能够理解自己和他人的情绪和动机",
    },
    
    # ========== 正义 (Justice) ==========
    {
        "id": 13,
        "question_number": 13,
        "text": "我在团队中能够很好地与他人合作，为共同目标努力",
        "category": "正义",
        "category_code": "justice",
        "strength": "团队合作",
        "strength_key": "teamwork",
        "description": "作为团队成员能够尽责合作，促进团队和谐",
    },
    {
        "id": 14,
        "question_number": 14,
        "text": "我重视公平，会确保每个人都得到应有的对待",
        "category": "正义",
        "category_code": "justice",
        "strength": "公平",
        "strength_key": "fairness",
        "description": "基于正义和公平的原则对待他人",
    },
    {
        "id": 15,
        "question_number": 15,
        "text": "我能够激励和引导他人，帮助他们发挥潜力",
        "category": "正义",
        "category_code": "justice",
        "strength": "领导力",
        "strength_key": "leadership",
        "description": "能够组织和激励团队成员达成共同目标",
    },
    
    # ========== 节制 (Temperance) ==========
    {
        "id": 16,
        "question_number": 16,
        "text": "我能够原谅曾经伤害过我的人，不会一直怀恨在心",
        "category": "节制",
        "category_code": "temperance",
        "strength": "宽恕",
        "strength_key": "forgiveness",
        "description": "能够原谅他人的过错，给予第二次机会",
    },
    {
        "id": 17,
        "question_number": 17,
        "text": "我对自己有客观的认识，不会过分炫耀自己的成就",
        "category": "节制",
        "category_code": "temperance",
        "strength": "谦逊",
        "strength_key": "humility",
        "description": "不过度关注自己，能够客观看待自己的优缺点",
    },
    {
        "id": 18,
        "question_number": 18,
        "text": "我在做决定时会谨慎考虑，不会冲动行事",
        "category": "节制",
        "category_code": "temperance",
        "strength": "审慎",
        "strength_key": "prudence",
        "description": "谨慎地做选择，避免不必要的风险",
    },
    {
        "id": 19,
        "question_number": 19,
        "text": "我能够控制自己的冲动和情绪，不会轻易被欲望左右",
        "category": "节制",
        "category_code": "temperance",
        "strength": "自我调节",
        "strength_key": "self_regulation",
        "description": "能够控制自己的冲动、情绪和行为",
    },
    
    # ========== 超越 (Transcendence) ==========
    {
        "id": 20,
        "question_number": 20,
        "text": "我能够欣赏艺术、自然和生活中的美好事物",
        "category": "超越",
        "category_code": "transcendence",
        "strength": "审美",
        "strength_key": "appreciation_of_beauty",
        "description": "能够欣赏和体验生活中的美好",
    },
    {
        "id": 21,
        "question_number": 21,
        "text": "我经常对生活中的好事心存感激，会表达我的感谢",
        "category": "超越",
        "category_code": "transcendence",
        "strength": "感恩",
        "strength_key": "gratitude",
        "description": "对生活中的美好事物心存感激并表达感谢",
    },
    {
        "id": 22,
        "question_number": 22,
        "text": "我对未来充满希望和乐观，相信事情会向好的方向发展",
        "category": "超越",
        "category_code": "transcendence",
        "strength": "希望",
        "strength_key": "hope",
        "description": "对未来抱有积极的期待，相信自己能够实现目标",
    },
    {
        "id": 23,
        "question_number": 23,
        "text": "我喜欢让周围的人开心，善于用幽默化解紧张气氛",
        "category": "超越",
        "category_code": "transcendence",
        "strength": "幽默",
        "strength_key": "humor",
        "description": "能够发现和创造快乐，让他人开心",
    },
    {
        "id": 24,
        "question_number": 24,
        "text": "我相信生命有更高的意义和目的，这给了我内心的指引",
        "category": "超越",
        "category_code": "transcendence",
        "strength": "灵性",
        "strength_key": "spirituality",
        "description": "对生命意义和更高目标有信念",
    },
]

# 按美德类别分组的题目
def get_questions_by_category(category_code: str) -> List[Dict[str, Any]]:
    """
    获取指定美德类别的题目
    
    Args:
        category_code: 美德类别代码 (wisdom/courage/humanity/justice/temperance/transcendence)
    
    Returns:
        该类别下的所有题目
    """
    return [q for q in VIA_QUESTIONS if q["category_code"] == category_code]

# 按优势获取题目
def get_question_by_strength(strength_key: str) -> Dict[str, Any] | None:
    """
    获取指定优势的题目
    
    Args:
        strength_key: 优势代码
    
    Returns:
        对应的题目，如果不存在返回None
    """
    for q in VIA_QUESTIONS:
        if q["strength_key"] == strength_key:
            return q
    return None

# 获取所有美德类别
VIRTUE_CATEGORY_LIST = [
    {"code": "wisdom", "name": "智慧与知识", "description": "获取和使用知识的认知优势"},
    {"code": "courage", "name": "勇气", "description": "面对困难时坚持达成目标的意志优势"},
    {"code": "humanity", "name": "人道", "description": "关心和帮助他人的人际优势"},
    {"code": "justice", "name": "正义", "description": "促进社区健康的公民优势"},
    {"code": "temperance", "name": "节制", "description": "防止过度的保护性优势"},
    {"code": "transcendence", "name": "超越", "description": "连接更广阔宇宙的意义优势"},
]

# 测评配置
ASSESSMENT_CONFIG = {
    "code": "VIA-24",
    "name": "VIA品格优势评估（简化版）",
    "version": "1.0.0",
    "description": "基于VIA性格优势分类的24题简化版测评，帮助您发现自己的核心优势",
    "total_questions": 24,
    "estimated_time_minutes": 8,
    "scoring_range": {"min": 1, "max": 5},
    "categories": 6,
    "strengths": 24,
}
