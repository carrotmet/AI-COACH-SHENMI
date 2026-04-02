# -*- coding: utf-8 -*-
"""
报表模板数据

包含三种类型的报表模板：
1. 引流报表（Quick Report）- 免费版，简洁易懂，高分享性
2. 深度报表（Full Report）- 付费版，专业详细，行动导向
3. 动态报表（Trend Report）- 趋势分析，长期追踪
"""

from typing import Dict, Any, List

# ========== 引流报表模板（免费版）==========
QUICK_REPORT_TEMPLATE = {
    "template_code": "quick_report",
    "name": "优势速览报告",
    "version": "1.0.0",
    "description": "简洁的优势概览报告，适合快速分享",
    "is_premium": False,
    
    # 报告结构
    "sections": [
        {
            "id": "cover",
            "name": "封面",
            "order": 1,
            "enabled": True,
        },
        {
            "id": "top_strengths",
            "name": "核心优势",
            "order": 2,
            "enabled": True,
        },
        {
            "id": "virtue_summary",
            "name": "美德领域概览",
            "order": 3,
            "enabled": True,
        },
        {
            "id": "quick_tips",
            "name": "快速建议",
            "order": 4,
            "enabled": True,
        },
        {
            "id": "cta",
            "name": "行动召唤",
            "order": 5,
            "enabled": True,
        },
    ],
    
    # 内容模板
    "content": {
        "cover": {
            "title": "你的性格优势报告",
            "subtitle": "基于VIA性格优势科学评估",
            "description": "每个人都有独特的优势组合，发现它们，发挥它们，成就更好的自己",
        },
        "top_strengths": {
            "title": "你的五大核心优势",
            "subtitle": "这些是你的突出优势，在生活和工作中多发挥它们",
            "strength_count": 5,
            "show_rank": True,
            "show_score": True,
            "show_description": True,
            "show_icon": True,
        },
        "virtue_summary": {
            "title": "你的优势分布",
            "subtitle": "六大美德领域的得分情况",
            "chart_type": "radar",  # radar / bar / pie
            "show_category_scores": True,
            "show_category_icons": True,
        },
        "quick_tips": {
            "title": "快速行动建议",
            "subtitle": "基于你的优势，这里有一些立即可行的建议",
            "tip_count": 3,
            "tips_template": [
                "在工作中寻找机会发挥你的{top_strength_1}，这会让你更有成就感",
                "利用你的{top_strength_2}优势，尝试学习一项新技能",
                "结合你的{top_strength_3}，设定一个本周可以实现的小目标",
            ],
        },
        "cta": {
            "title": "探索更多可能",
            "description": "获取完整版报告，深入了解全部24项优势，获得个性化发展建议",
            "button_text": "解锁完整报告",
            "features": [
                "完整的24项优势分析",
                "详细的发展建议",
                "个性化行动计划",
                "AI优势教练对话",
            ],
        },
    },
    
    # 视觉配置
    "visual": {
        "theme": "modern",
        "primary_color": "#6366F1",
        "secondary_color": "#8B5CF6",
        "accent_color": "#F59E0B",
        "background_color": "#FFFFFF",
        "font_family": "system-ui, -apple-system, sans-serif",
        "card_style": "rounded",
        "animation": True,
    },
    
    # 分享配置
    "sharing": {
        "enabled": True,
        "share_title": "我发现了自己的性格优势！",
        "share_description": "基于VIA科学测评，我的核心优势是：{top_strengths}",
        "share_image": "generate",  # generate / static
        "show_share_buttons": ["wechat", "weibo", "copy_link"],
    },
}

# ========== 深度报表模板（付费版）==========
FULL_REPORT_TEMPLATE = {
    "template_code": "full_report",
    "name": "完整优势分析报告",
    "version": "1.0.0",
    "description": "专业详细的完整优势分析报告，包含全部24项优势深度解读",
    "is_premium": True,
    
    # 报告结构
    "sections": [
        {
            "id": "cover",
            "name": "封面",
            "order": 1,
            "enabled": True,
        },
        {
            "id": "executive_summary",
            "name": "执行摘要",
            "order": 2,
            "enabled": True,
        },
        {
            "id": "top_strengths_detail",
            "name": "核心优势详解",
            "order": 3,
            "enabled": True,
        },
        {
            "id": "all_strengths_ranking",
            "name": "完整优势排序",
            "order": 4,
            "enabled": True,
        },
        {
            "id": "virtue_analysis",
            "name": "美德领域分析",
            "order": 5,
            "enabled": True,
        },
        {
            "id": "strength_combinations",
            "name": "优势组合分析",
            "order": 6,
            "enabled": True,
        },
        {
            "id": "development_plan",
            "name": "发展计划",
            "order": 7,
            "enabled": True,
        },
        {
            "id": "action_items",
            "name": "行动清单",
            "order": 8,
            "enabled": True,
        },
        {
            "id": "resources",
            "name": "推荐资源",
            "order": 9,
            "enabled": True,
        },
    ],
    
    # 内容模板
    "content": {
        "cover": {
            "title": "完整性格优势分析报告",
            "subtitle": "基于VIA性格优势分类的深度解读",
            "description": "全面了解自己的24项性格优势，发现独特的优势组合，制定个性化发展计划",
        },
        "executive_summary": {
            "title": "你的优势概览",
            "sections": [
                {
                    "id": "profile_overview",
                    "title": "优势档案概览",
                    "content_template": """
                    根据VIA性格优势评估，你的优势档案呈现出以下特点：
                    
                    **核心优势领域**：{dominant_virtue}
                    你在{dominant_virtue}方面表现最为突出，这反映了你对{virtue_description}的重视。
                    
                    **优势分布特点**：{distribution_pattern}
                    你的优势分布{distribution_description}，这表明你是一个{personality_description}的人。
                    
                    **发展建议重点**：建议重点关注{development_focus}，这将帮助你更好地发挥整体优势。
                    """,
                },
                {
                    "id": "key_insights",
                    "title": "关键洞察",
                    "content_template": """
                    - 你的最强优势是**{top_strength}**，这让你在{strength_application}方面具有天然优势
                    - 你的前5大优势集中在{virtue_concentration}领域，形成了独特的优势组合
                    - 你的优势模式适合{career_suggestion}类型的工作和发展方向
                    """,
                },
            ],
        },
        "top_strengths_detail": {
            "title": "你的五大核心优势深度解读",
            "subtitle": "详细了解你的最强优势，以及如何更好地发挥它们",
            "strength_count": 5,
            "detail_sections": [
                "definition",  # 定义
                "your_profile",  # 你的表现
                "applications",  # 应用场景
                "development_tips",  # 发展建议
                "related_strengths",  # 相关优势
            ],
        },
        "all_strengths_ranking": {
            "title": "完整优势排序",
            "subtitle": "全部24项性格优势的得分排名",
            "display_mode": "ranked_list",  # ranked_list / category_grid
            "show_percentile": True,
            "show_comparison": True,
            "group_by_virtue": True,
        },
        "virtue_analysis": {
            "title": "六大美德领域深度分析",
            "subtitle": "了解你在每个美德领域的表现",
            "virtues": ["wisdom", "courage", "humanity", "justice", "temperance", "transcendence"],
            "analysis_sections": [
                "score_interpretation",  # 得分解读
                "strengths_in_category",  # 该领域优势
                "development_opportunities",  # 发展机会
                "practical_applications",  # 实际应用
            ],
        },
        "strength_combinations": {
            "title": "你的优势组合分析",
            "subtitle": "了解你的优势如何协同工作",
            "combination_types": [
                {
                    "name": "黄金三角",
                    "description": "你的前三大优势形成的独特组合",
                    "template": "你的{strength_1}、{strength_2}和{strength_3}形成了强大的优势组合，让你在{combination_benefit}方面具有突出能力。",
                },
                {
                    "name": "互补优势",
                    "description": "能够相互补充的优势对",
                    "template": "你的{strength_a}和{strength_b}相互补充，帮助你在{complementary_area}取得更好表现。",
                },
                {
                    "name": "潜在协同",
                    "description": "可以进一步发展的优势组合",
                    "template": "结合你的{strength_x}和{strength_y}，你可以在{synergy_area}创造更大价值。",
                },
            ],
        },
        "development_plan": {
            "title": "个性化发展计划",
            "subtitle": "基于你的优势档案，制定专属发展计划",
            "plan_sections": [
                {
                    "id": "leverage_top",
                    "title": "发挥核心优势",
                    "timeframe": "立即开始",
                    "template": """
                    **目标**：最大化发挥你的{top_strength}优势
                    
                    **行动步骤**：
                    1. 在工作中主动承担需要{strength_application}的任务
                    2. 每周至少一次刻意使用这一优势
                    3. 记录使用这一优势的成功案例
                    4. 帮助他人发展这方面的能力
                    
                    **预期成果**：在{expected_outcome}方面获得显著提升
                    """,
                },
                {
                    "id": "develop_mid",
                    "title": "培养潜力优势",
                    "timeframe": "3个月内",
                    "template": """
                    **目标**：提升你的{mid_strength}到更高水平
                    
                    **行动步骤**：
                    1. 每天练习使用这一优势15分钟
                    2. 寻找能够应用这一优势的场景
                    3. 向在这一方面有优势的人学习
                    4. 定期反思和评估进步
                    
                    **预期成果**：这一优势成为你新的突出优势
                    """,
                },
                {
                    "id": "balance_profile",
                    "title": "平衡优势档案",
                    "timeframe": "6个月内",
                    "template": """
                    **目标**：建立更加平衡的优势组合
                    
                    **行动步骤**：
                    1. 识别需要关注的{development_area}
                    2. 寻找能够弥补这一领域的合作伙伴
                    3. 在必要时进行基础练习
                    4. 不要过分关注不足，而是发挥核心优势
                    
                    **预期成果**：形成更加全面和平衡的优势档案
                    """,
                },
            ],
        },
        "action_items": {
            "title": "30天行动清单",
            "subtitle": "立即可执行的具体行动",
            "items_per_week": 3,
            "weeks": 4,
            "template": [
                {
                    "week": 1,
                    "theme": "发现优势",
                    "actions": [
                        "每天记录一次使用{top_strength}的经历",
                        "向3位朋友询问他们认为你的优势是什么",
                        "回顾过去一年的成就，找出背后的优势",
                    ],
                },
                {
                    "week": 2,
                    "theme": "应用优势",
                    "actions": [
                        "在工作中找到一个发挥{top_strength}的机会",
                        "用{second_strength}帮助一位朋友或同事",
                        "尝试将{top_strength}应用到一个新领域",
                    ],
                },
                {
                    "week": 3,
                    "theme": "深化优势",
                    "actions": [
                        "学习一个与{top_strength}相关的新技能",
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
            ],
        },
        "resources": {
            "title": "推荐资源",
            "subtitle": "帮助你进一步发挥优势的精选资源",
            "resource_types": [
                {
                    "type": "book",
                    "title": "书籍推荐",
                    "items": [
                        {"title": "优势识别器2.0", "author": "汤姆·拉思", "description": "深入了解盖洛普优势理论"},
                        {"title": "性格优势与美德", "author": "塞利格曼", "description": "VIA优势的理论基础"},
                        {"title": "现在，发现你的优势", "author": "马库斯·白金汉", "description": "实用的优势发展指南"},
                    ],
                },
                {
                    "type": "tool",
                    "title": "实用工具",
                    "items": [
                        {"title": "优势日记", "description": "每天记录优势使用情况"},
                        {"title": "优势行动计划模板", "description": "制定具体的发展计划"},
                        {"title": "优势对话指南", "description": "与他人讨论优势的方法"},
                    ],
                },
                {
                    "type": "feature",
                    "title": "平台功能",
                    "items": [
                        {"title": "AI优势教练", "description": "与AI教练深入探讨你的优势"},
                        {"title": "优势发展练习", "description": "针对性的优势强化练习"},
                        {"title": "成长目标追踪", "description": "设定和追踪基于优势的目标"},
                    ],
                },
            ],
        },
    },
    
    # 视觉配置
    "visual": {
        "theme": "professional",
        "primary_color": "#4F46E5",
        "secondary_color": "#7C3AED",
        "accent_color": "#F59E0B",
        "background_color": "#FAFAFA",
        "card_background": "#FFFFFF",
        "font_family": "system-ui, -apple-system, sans-serif",
        "card_style": "elevated",
        "animation": True,
        "charts": {
            "radar_chart": True,
            "bar_chart": True,
            "line_chart": True,
            "word_cloud": True,
        },
    },
    
    # 导出配置
    "export": {
        "pdf": {
            "enabled": True,
            "page_size": "A4",
            "orientation": "portrait",
            "include_cover": True,
            "include_toc": True,
        },
        "image": {
            "enabled": True,
            "formats": ["png", "jpg"],
            "resolutions": ["1x", "2x"],
        },
    },
}

# ========== 动态报表模板（趋势分析）==========
TREND_REPORT_TEMPLATE = {
    "template_code": "trend_report",
    "name": "优势发展趋势报告",
    "version": "1.0.0",
    "description": "追踪优势发展的长期趋势，可视化成长轨迹",
    "is_premium": True,
    
    # 报告结构
    "sections": [
        {
            "id": "overview",
            "name": "趋势概览",
            "order": 1,
            "enabled": True,
        },
        {
            "id": "strength_trends",
            "name": "优势趋势分析",
            "order": 2,
            "enabled": True,
        },
        {
            "id": "virtue_trends",
            "name": "美德领域趋势",
            "order": 3,
            "enabled": True,
        },
        {
            "id": "progress_insights",
            "name": "进步洞察",
            "order": 4,
            "enabled": True,
        },
        {
            "id": "recommendations",
            "name": "发展建议",
            "order": 5,
            "enabled": True,
        },
    ],
    
    # 内容模板
    "content": {
        "overview": {
            "title": "你的优势发展轨迹",
            "subtitle": "追踪你的成长历程",
            "metrics": [
                {
                    "id": "assessment_count",
                    "name": "测评次数",
                    "description": "已完成{count}次测评",
                },
                {
                    "id": "time_span",
                    "name": "追踪时长",
                    "description": "已追踪{days}天",
                },
                {
                    "id": "top_strength_stability",
                    "name": "核心优势稳定性",
                    "description": "你的前3大优势保持稳定",
                },
                {
                    "id": "improvement_areas",
                    "name": "进步领域",
                    "description": "{count}个优势有明显提升",
                },
            ],
        },
        "strength_trends": {
            "title": "各项优势发展趋势",
            "subtitle": "查看每项优势的变化轨迹",
            "chart_types": ["line", "area", "heatmap"],
            "time_ranges": ["3个月", "6个月", "1年", "全部"],
        },
        "virtue_trends": {
            "title": "美德领域发展趋势",
            "subtitle": "六大美德领域的整体变化",
            "chart_type": "stacked_area",
            "show_balance_score": True,
        },
        "progress_insights": {
            "title": "进步洞察",
            "subtitle": "基于数据分析的关键发现",
            "insight_types": [
                {
                    "id": "improved_strengths",
                    "title": "显著提升的优势",
                    "template": "你的{strength_name}在过去{time_period}提升了{improvement_points}分，这表明你的努力正在产生效果。",
                },
                {
                    "id": "consistent_strengths",
                    "title": "稳定的核心优势",
                    "template": "你的{strength_name}始终保持在高水平，这是你的稳定优势领域。",
                },
                {
                    "id": "emerging_strengths",
                    "title": "新兴优势",
                    "template": "你的{strength_name}正在快速发展，有望成为新的核心优势。",
                },
                {
                    "id": "balance_changes",
                    "title": "平衡性变化",
                    "template": "你的优势档案{balance_change_description}，整体{balance_trend}。",
                },
            ],
        },
        "recommendations": {
            "title": "基于趋势的发展建议",
            "subtitle": "根据你的发展趋势，提供个性化建议",
            "template": [
                "继续保持{consistent_strength}的优势，这是你最大的资产",
                "重点发展{improving_strength}，它已经显示出良好的进步趋势",
                "关注{development_area}，这可以帮助你建立更平衡的优势档案",
            ],
        },
    },
    
    # 视觉配置
    "visual": {
        "theme": "modern",
        "primary_color": "#10B981",
        "secondary_color": "#3B82F6",
        "accent_color": "#F59E0B",
        "charts": {
            "line_chart": True,
            "area_chart": True,
            "heatmap": True,
            "sparkline": True,
        },
    },
}

# 报告生成配置
REPORT_GENERATION_CONFIG = {
    "cache_duration_minutes": 60,
    "max_reports_per_day": 10,
    "pdf_generation_timeout_seconds": 30,
    "image_generation_timeout_seconds": 15,
    "default_language": "zh-CN",
    "supported_languages": ["zh-CN", "en-US"],
}

# 报告类型映射
REPORT_TYPE_MAPPING = {
    "quick": QUICK_REPORT_TEMPLATE,
    "full": FULL_REPORT_TEMPLATE,
    "trend": TREND_REPORT_TEMPLATE,
}


def get_report_template(template_code: str) -> Dict[str, Any] | None:
    """
    获取报表模板
    
    Args:
        template_code: 模板代码 (quick/full/trend)
    
    Returns:
        报表模板配置
    """
    return REPORT_TYPE_MAPPING.get(template_code)


def get_all_templates() -> List[Dict[str, Any]]:
    """
    获取所有可用模板
    
    Returns:
        所有模板列表
    """
    return list(REPORT_TYPE_MAPPING.values())


def get_premium_templates() -> List[Dict[str, Any]]:
    """
    获取付费模板
    
    Returns:
        付费模板列表
    """
    return [t for t in REPORT_TYPE_MAPPING.values() if t.get("is_premium")]


def get_free_templates() -> List[Dict[str, Any]]:
    """
    获取免费模板
    
    Returns:
        免费模板列表
    """
    return [t for t in REPORT_TYPE_MAPPING.values() if not t.get("is_premium")]
