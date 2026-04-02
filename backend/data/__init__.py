# -*- coding: utf-8 -*-
"""
深觅 AI Coach - 数据模块

包含测评题目、优势定义、报表模板等静态数据
"""

from data.via_questions import VIA_QUESTIONS, VIA_QUESTION_OPTIONS
from data.strength_data import VIA_STRENGTHS, VIRTUE_CATEGORIES, STRENGTH_DEVELOPMENT_TIPS
from data.report_templates import QUICK_REPORT_TEMPLATE, FULL_REPORT_TEMPLATE, TREND_REPORT_TEMPLATE

__all__ = [
    "VIA_QUESTIONS",
    "VIA_QUESTION_OPTIONS", 
    "VIA_STRENGTHS",
    "VIRTUE_CATEGORIES",
    "STRENGTH_DEVELOPMENT_TIPS",
    "QUICK_REPORT_TEMPLATE",
    "FULL_REPORT_TEMPLATE",
    "TREND_REPORT_TEMPLATE",
]
