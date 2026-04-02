# -*- coding: utf-8 -*-
"""
深觅 AI Coach - 服务模块

包含所有业务逻辑服务
"""

from services.scoring_engine import (
    ScoringEngine,
    AssessmentResult,
    StrengthScore,
    VirtueScore,
    get_scoring_engine,
)
from services.assessment_service import (
    AssessmentService,
    AssessmentSession,
    AssessmentStatus,
    AssessmentType,
    get_assessment_service,
)
from services.report_service import (
    ReportService,
    Report,
    ReportType,
    ReportStatus,
    get_report_service,
)
from services.chat_service import (
    ChatService,
    Conversation,
    Message,
    ChatResponse,
    ConversationStatus,
    MessageRole,
    get_chat_service,
    init_chat_service,
)
from services.llm_service import (
    LLMService,
    LLMConfig,
    LLMResponse,
    LLMProvider,
    get_llm_service,
    init_llm_service,
    quick_chat,
)
from services.litellm_service import (
    LiteLLMService,
    LiteLLMConfig,
    CoachIntent,
    UserInsight,
    SessionSummary,
    get_litellm_service,
    init_litellm_service,
)
from services.emotion_analyzer import (
    EmotionAnalyzer,
    EmotionAnalysisResult,
    EmotionType,
    SentimentType,
    get_emotion_analyzer,
    init_emotion_analyzer,
    analyze_emotion,
)
from services.auth_service import AuthService

__all__ = [
    # 评分引擎
    "ScoringEngine",
    "AssessmentResult",
    "StrengthScore",
    "VirtueScore",
    "get_scoring_engine",
    # 测评服务
    "AssessmentService",
    "AssessmentSession",
    "AssessmentStatus",
    "AssessmentType",
    "get_assessment_service",
    # 报表服务
    "ReportService",
    "Report",
    "ReportType",
    "ReportStatus",
    "get_report_service",
    # 对话服务
    "ChatService",
    "Conversation",
    "Message",
    "ChatResponse",
    "ConversationStatus",
    "MessageRole",
    "get_chat_service",
    "init_chat_service",
    # LLM服务
    "LLMService",
    "LLMConfig",
    "LLMResponse",
    "LLMProvider",
    "get_llm_service",
    "init_llm_service",
    "quick_chat",
    # LiteLLM服务 (v2)
    "LiteLLMService",
    "LiteLLMConfig",
    "CoachIntent",
    "UserInsight",
    "SessionSummary",
    "get_litellm_service",
    "init_litellm_service",
    # 情感分析
    "EmotionAnalyzer",
    "EmotionAnalysisResult",
    "EmotionType",
    "SentimentType",
    "get_emotion_analyzer",
    "init_emotion_analyzer",
    "analyze_emotion",
    # 认证服务
    "AuthService",
]
