# -*- coding: utf-8 -*-
"""
深觅 AI Coach - SQLAlchemy模型定义

该模块定义了所有数据库表的ORM模型
基于schema.sql创建
"""

from datetime import datetime, date
from typing import Optional, List, Dict, Any
from enum import Enum as PyEnum

from sqlalchemy import (
    Column,
    Integer,
    String,
    Text,
    Boolean,
    DateTime,
    Date,
    Float,
    ForeignKey,
    CheckConstraint,
    JSON,
)
from sqlalchemy.orm import DeclarativeBase, relationship
from sqlalchemy.sql import func


# =====================================================
# 基础模型类
# =====================================================
class Base(DeclarativeBase):
    """SQLAlchemy基础模型类"""
    pass


# =====================================================
# 枚举类型定义
# =====================================================
class UserStatus(str, PyEnum):
    """用户状态"""
    ACTIVE = "active"
    INACTIVE = "inactive"
    SUSPENDED = "suspended"
    DELETED = "deleted"


class SubscriptionType(str, PyEnum):
    """订阅类型"""
    FREE = "free"
    BASIC = "basic"
    PREMIUM = "premium"
    ENTERPRISE = "enterprise"


class TokenType(str, PyEnum):
    """令牌类型"""
    ACCESS = "access"
    REFRESH = "refresh"
    API = "api"


class ConversationStatus(str, PyEnum):
    """对话状态"""
    ACTIVE = "active"
    ARCHIVED = "archived"
    DELETED = "deleted"


class CoachType(str, PyEnum):
    """教练类型"""
    STRENGTH = "strength"
    CAREER = "career"
    RELATIONSHIP = "relationship"
    WELLNESS = "wellness"
    GENERAL = "general"


class MessageRole(str, PyEnum):
    """消息角色"""
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"
    COACH = "coach"


class AssessmentType(str, PyEnum):
    """评估类型"""
    VIA_STRENGTHS = "via_strengths"
    MBTI = "mbti"
    DISC = "disc"
    BIG_FIVE = "big_five"
    CUSTOM = "custom"
    WEEKLY_CHECKIN = "weekly_checkin"
    GOAL_PROGRESS = "goal_progress"


class AssessmentStatus(str, PyEnum):
    """评估状态"""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    EXPIRED = "expired"
    CANCELLED = "cancelled"


class GoalStatus(str, PyEnum):
    """目标状态"""
    DRAFT = "draft"
    ACTIVE = "active"
    PAUSED = "paused"
    COMPLETED = "completed"
    ABANDONED = "abandoned"


class GoalCategory(str, PyEnum):
    """目标类别"""
    CAREER = "career"
    RELATIONSHIP = "relationship"
    HEALTH = "health"
    LEARNING = "learning"
    FINANCE = "finance"
    PERSONAL = "personal"
    OTHER = "other"


class Priority(str, PyEnum):
    """优先级"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"


class Visibility(str, PyEnum):
    """可见性"""
    PRIVATE = "private"
    COACH_ONLY = "coach_only"
    PUBLIC = "public"


class SubscriptionStatus(str, PyEnum):
    """订阅状态"""
    ACTIVE = "active"
    CANCELLED = "cancelled"
    EXPIRED = "expired"
    SUSPENDED = "suspended"
    TRIAL = "trial"


class BillingCycle(str, PyEnum):
    """计费周期"""
    MONTHLY = "monthly"
    QUARTERLY = "quarterly"
    YEARLY = "yearly"


class PaymentStatus(str, PyEnum):
    """支付状态"""
    PENDING = "pending"
    COMPLETED = "completed"
    FAILED = "failed"
    REFUNDED = "refunded"
    CANCELLED = "cancelled"


class PaymentType(str, PyEnum):
    """支付类型"""
    SUBSCRIPTION = "subscription"
    ONE_TIME = "one_time"
    REFUND = "refund"
    CREDIT = "credit"


class QuotaPeriod(str, PyEnum):
    """配额周期"""
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"


class NotificationType(str, PyEnum):
    """通知类型"""
    SYSTEM = "system"
    COACH = "coach"
    GOAL = "goal"
    ASSESSMENT = "assessment"
    SUBSCRIPTION = "subscription"
    REMINDER = "reminder"


class VirtueCategory(str, PyEnum):
    """美德类别"""
    WISDOM = "智慧"
    COURAGE = "勇气"
    HUMANITY = "仁爱"
    JUSTICE = "正义"
    TEMPERANCE = "节制"
    TRANSCENDENCE = "超越"


class PromptType(str, PyEnum):
    """提示词类型"""
    SYSTEM = "system"
    GREETING = "greeting"
    STRENGTH_ANALYSIS = "strength_analysis"
    GOAL_SETTING = "goal_setting"
    ACTION_PLANNING = "action_planning"
    REFLECTION = "reflection"
    ENCOURAGEMENT = "encouragement"
    CRISIS_SUPPORT = "crisis_support"


class LogLevel(str, PyEnum):
    """日志级别"""
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


# =====================================================
# 1. 用户管理相关表
# =====================================================

class User(Base):
    """用户基础信息表"""
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String(50), unique=True, nullable=False)
    email = Column(String(255), unique=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    phone = Column(String(20), unique=True)
    avatar_url = Column(Text)
    status = Column(
        String(20),
        default=UserStatus.ACTIVE.value,
        nullable=False
    )
    subscription_type = Column(
        String(20),
        default=SubscriptionType.FREE.value,
        nullable=False
    )
    email_verified = Column(Boolean, default=False)
    phone_verified = Column(Boolean, default=False)
    last_login_at = Column(DateTime)
    created_at = Column(DateTime, default=func.current_timestamp())
    updated_at = Column(DateTime, default=func.current_timestamp())
    deleted_at = Column(DateTime)  # 软删除标记
    
    # 关系定义
    profile = relationship("UserProfile", back_populates="user", uselist=False)
    tokens = relationship("UserToken", back_populates="user")
    conversations = relationship("Conversation", back_populates="user")
    assessments = relationship("Assessment", back_populates="user")
    goals = relationship("Goal", back_populates="user")
    subscriptions = relationship("Subscription", back_populates="user")
    payments = relationship("Payment", back_populates="user")
    notifications = relationship("Notification", back_populates="user")
    usage_quota = relationship("UsageQuota", back_populates="user", uselist=False)


class UserProfile(Base):
    """用户画像表"""
    __tablename__ = "user_profiles"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False)
    nickname = Column(String(50))
    gender = Column(String(10))
    birth_date = Column(Date)
    occupation = Column(String(100))
    company = Column(String(100))
    industry = Column(String(50))
    location = Column(String(100))
    bio = Column(Text)
    goals = Column(Text)  # 用户目标描述
    interests = Column(Text)  # 兴趣爱好
    strengths_profile = Column(JSON)  # 优势档案
    personality_type = Column(String(10))  # MBTI等
    preferences = Column(JSON)  # 用户偏好设置
    coaching_style_preference = Column(String(20))
    notification_settings = Column(JSON, default={
        "email": True,
        "push": True,
        "sms": False
    })
    privacy_settings = Column(JSON, default={
        "profile_visible": False,
        "share_anonymous_data": True
    })
    created_at = Column(DateTime, default=func.current_timestamp())
    updated_at = Column(DateTime, default=func.current_timestamp())
    
    # 关系定义
    user = relationship("User", back_populates="profile")


class UserToken(Base):
    """用户认证令牌表"""
    __tablename__ = "user_tokens"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    token_type = Column(String(20), nullable=False)
    token_hash = Column(String(255), nullable=False)
    device_info = Column(JSON)
    ip_address = Column(String(45))
    expires_at = Column(DateTime, nullable=False)
    created_at = Column(DateTime, default=func.current_timestamp())
    last_used_at = Column(DateTime)
    revoked = Column(Boolean, default=False)
    
    # 关系定义
    user = relationship("User", back_populates="tokens")


# =====================================================
# 2. 对话系统相关表
# =====================================================

class Conversation(Base):
    """对话会话表"""
    __tablename__ = "conversations"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    title = Column(String(200), default="新对话")
    status = Column(String(20), default=ConversationStatus.ACTIVE.value)
    coach_type = Column(String(30), default=CoachType.STRENGTH.value)
    context = Column(JSON)  # 对话上下文
    _metadata = Column(JSON)  # 元数据
    message_count = Column(Integer, default=0)
    started_at = Column(DateTime, default=func.current_timestamp())
    ended_at = Column(DateTime)
    created_at = Column(DateTime, default=func.current_timestamp())
    updated_at = Column(DateTime, default=func.current_timestamp())
    
    # 关系定义
    user = relationship("User", back_populates="conversations")
    messages = relationship("Message", back_populates="conversation")
    summary = relationship("ConversationSummary", back_populates="conversation", uselist=False)


class Message(Base):
    """消息记录表"""
    __tablename__ = "messages"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    conversation_id = Column(Integer, ForeignKey("conversations.id", ondelete="CASCADE"), nullable=False)
    role = Column(String(20), nullable=False)
    content = Column(Text, nullable=False)
    content_type = Column(String(20), default="text")
    emotion_tag = Column(String(30))
    sentiment_score = Column(Float)
    model_info = Column(JSON)
    tokens_used = Column(Integer)
    response_time_ms = Column(Integer)
    is_edited = Column(Boolean, default=False)
    edited_at = Column(DateTime)
    parent_message_id = Column(Integer, ForeignKey("messages.id", ondelete="SET NULL"))
    attachments = Column(JSON)
    _metadata = Column(JSON)
    created_at = Column(DateTime, default=func.current_timestamp())
    
    # 关系定义
    conversation = relationship("Conversation", back_populates="messages")


class ConversationSummary(Base):
    """对话摘要表"""
    __tablename__ = "conversation_summaries"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    conversation_id = Column(Integer, ForeignKey("conversations.id", ondelete="CASCADE"), unique=True, nullable=False)
    summary = Column(Text)
    key_points = Column(JSON)
    action_items = Column(JSON)
    topics = Column(JSON)
    sentiment_overview = Column(String(50))
    generated_at = Column(DateTime, default=func.current_timestamp())
    updated_at = Column(DateTime, default=func.current_timestamp())
    
    # 关系定义
    conversation = relationship("Conversation", back_populates="summary")


# =====================================================
# 3. 评估系统相关表
# =====================================================

class Assessment(Base):
    """评估记录表"""
    __tablename__ = "assessments"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    assessment_type = Column(String(30), nullable=False)
    title = Column(String(200))
    description = Column(Text)
    status = Column(String(20), default=AssessmentStatus.PENDING.value)
    version = Column(String(10), default="1.0")
    score_summary = Column(JSON)
    interpretation = Column(Text)
    recommendations = Column(JSON)
    started_at = Column(DateTime)
    completed_at = Column(DateTime)
    valid_until = Column(DateTime)
    created_at = Column(DateTime, default=func.current_timestamp())
    updated_at = Column(DateTime, default=func.current_timestamp())
    
    # 关系定义
    user = relationship("User", back_populates="assessments")
    results = relationship("AssessmentResult", back_populates="assessment")
    responses = relationship("AssessmentResponse", back_populates="assessment")


class AssessmentResult(Base):
    """评估结果详情表"""
    __tablename__ = "assessment_results"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    assessment_id = Column(Integer, ForeignKey("assessments.id", ondelete="CASCADE"), nullable=False)
    dimension_name = Column(String(100), nullable=False)
    dimension_code = Column(String(50))
    category = Column(String(50))
    score = Column(Float, nullable=False)
    normalized_score = Column(Float)
    percentile = Column(Integer)
    rank = Column(Integer)
    interpretation = Column(Text)
    strengths_description = Column(Text)
    development_tips = Column(Text)
    related_strengths = Column(JSON)
    _metadata = Column(JSON)
    created_at = Column(DateTime, default=func.current_timestamp())
    
    # 关系定义
    assessment = relationship("Assessment", back_populates="results")


class AssessmentResponse(Base):
    """评估答题记录表"""
    __tablename__ = "assessment_responses"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    assessment_id = Column(Integer, ForeignKey("assessments.id", ondelete="CASCADE"), nullable=False)
    question_id = Column(String(50), nullable=False)
    question_text = Column(Text)
    response_value = Column(Text, nullable=False)
    response_score = Column(Float)
    response_time_ms = Column(Integer)
    created_at = Column(DateTime, default=func.current_timestamp())
    
    # 关系定义
    assessment = relationship("Assessment", back_populates="responses")


# =====================================================
# 4. 目标管理相关表
# =====================================================

class Goal(Base):
    """用户目标表"""
    __tablename__ = "goals"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    title = Column(String(200), nullable=False)
    description = Column(Text)
    category = Column(String(50))
    status = Column(String(20), default=GoalStatus.ACTIVE.value)
    priority = Column(String(10), default=Priority.MEDIUM.value)
    visibility = Column(String(20), default=Visibility.PRIVATE.value)
    deadline = Column(Date)
    start_date = Column(Date)
    completed_at = Column(DateTime)
    progress_percentage = Column(Integer, default=0)
    related_strengths = Column(JSON)
    success_criteria = Column(Text)
    obstacles = Column(Text)
    support_needed = Column(Text)
    progress_notes = Column(Text)
    created_at = Column(DateTime, default=func.current_timestamp())
    updated_at = Column(DateTime, default=func.current_timestamp())
    
    # 关系定义
    user = relationship("User", back_populates="goals")
    milestones = relationship("GoalMilestone", back_populates="goal")
    progress_records = relationship("GoalProgress", back_populates="goal")


class GoalMilestone(Base):
    """目标里程碑表"""
    __tablename__ = "goal_milestones"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    goal_id = Column(Integer, ForeignKey("goals.id", ondelete="CASCADE"), nullable=False)
    title = Column(String(200), nullable=False)
    description = Column(Text)
    status = Column(String(20), default="pending")
    target_date = Column(Date)
    completed_at = Column(DateTime)
    order_index = Column(Integer, default=0)
    created_at = Column(DateTime, default=func.current_timestamp())
    updated_at = Column(DateTime, default=func.current_timestamp())
    
    # 关系定义
    goal = relationship("Goal", back_populates="milestones")


class GoalProgress(Base):
    """目标进展记录表"""
    __tablename__ = "goal_progress"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    goal_id = Column(Integer, ForeignKey("goals.id", ondelete="CASCADE"), nullable=False)
    progress_type = Column(String(30), default="check_in")
    content = Column(Text, nullable=False)
    progress_value = Column(Integer)
    emotion_tag = Column(String(30))
    related_conversation_id = Column(Integer, ForeignKey("conversations.id", ondelete="SET NULL"))
    created_at = Column(DateTime, default=func.current_timestamp())
    
    # 关系定义
    goal = relationship("Goal", back_populates="progress_records")


# =====================================================
# 5. 订阅与支付相关表
# =====================================================

class Subscription(Base):
    """订阅表"""
    __tablename__ = "subscriptions"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    plan_type = Column(String(20), nullable=False)
    billing_cycle = Column(String(20), default=BillingCycle.MONTHLY.value)
    status = Column(String(20), default=SubscriptionStatus.ACTIVE.value)
    price = Column(Float, nullable=False)
    currency = Column(String(3), default="CNY")
    start_date = Column(Date, nullable=False)
    end_date = Column(Date)
    trial_end_date = Column(Date)
    auto_renew = Column(Boolean, default=True)
    payment_provider = Column(String(50))
    provider_subscription_id = Column(String(255))
    cancellation_reason = Column(Text)
    cancelled_at = Column(DateTime)
    created_at = Column(DateTime, default=func.current_timestamp())
    updated_at = Column(DateTime, default=func.current_timestamp())
    
    # 关系定义
    user = relationship("User", back_populates="subscriptions")
    payments = relationship("Payment", back_populates="subscription")


class Payment(Base):
    """支付记录表"""
    __tablename__ = "payments"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    subscription_id = Column(Integer, ForeignKey("subscriptions.id", ondelete="SET NULL"))
    payment_type = Column(String(20), default=PaymentType.SUBSCRIPTION.value)
    amount = Column(Float, nullable=False)
    currency = Column(String(3), default="CNY")
    status = Column(String(20), default=PaymentStatus.PENDING.value)
    payment_method = Column(String(50))
    payment_provider = Column(String(50))
    provider_transaction_id = Column(String(255))
    description = Column(Text)
    _metadata = Column(JSON)
    paid_at = Column(DateTime)
    created_at = Column(DateTime, default=func.current_timestamp())
    
    # 关系定义
    user = relationship("User", back_populates="payments")
    subscription = relationship("Subscription", back_populates="payments")


class UsageQuota(Base):
    """使用配额表"""
    __tablename__ = "usage_quotas"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False)
    plan_type = Column(String(20), nullable=False)
    conversation_limit = Column(Integer, default=10)
    conversation_used = Column(Integer, default=0)
    message_limit = Column(Integer, default=100)
    message_used = Column(Integer, default=0)
    assessment_limit = Column(Integer, default=1)
    assessment_used = Column(Integer, default=0)
    ai_call_limit = Column(Integer, default=100)
    ai_call_used = Column(Integer, default=0)
    quota_period = Column(String(20), default=QuotaPeriod.MONTHLY.value)
    period_start = Column(Date)
    period_end = Column(Date)
    extra_quota = Column(JSON)
    created_at = Column(DateTime, default=func.current_timestamp())
    updated_at = Column(DateTime, default=func.current_timestamp())
    
    # 关系定义
    user = relationship("User", back_populates="usage_quota")


# =====================================================
# 6. 教练知识库相关表
# =====================================================

class StrengthDefinition(Base):
    """优势定义表 (VIA 24种性格优势)"""
    __tablename__ = "strength_definitions"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    strength_key = Column(String(50), unique=True, nullable=False)
    name_zh = Column(String(100), nullable=False)
    name_en = Column(String(100), nullable=False)
    virtue_category = Column(String(50), nullable=False)
    definition = Column(Text, nullable=False)
    description = Column(Text)
    characteristics = Column(JSON)
    applications = Column(JSON)
    development_tips = Column(Text)
    overuse_risks = Column(Text)
    related_strengths = Column(JSON)
    famous_examples = Column(JSON)
    assessment_questions = Column(JSON)
    icon_url = Column(Text)
    color_code = Column(String(7))
    sort_order = Column(Integer)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=func.current_timestamp())
    updated_at = Column(DateTime, default=func.current_timestamp())


class CoachPrompt(Base):
    """教练提示词模板表"""
    __tablename__ = "coach_prompts"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    prompt_type = Column(String(50), nullable=False)
    name = Column(String(100), nullable=False)
    description = Column(Text)
    template = Column(Text, nullable=False)
    variables = Column(JSON)
    context_conditions = Column(JSON)
    priority = Column(Integer, default=0)
    is_default = Column(Boolean, default=False)
    model_config = Column(JSON)
    usage_count = Column(Integer, default=0)
    success_rate = Column(Float)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=func.current_timestamp())
    updated_at = Column(DateTime, default=func.current_timestamp())


# =====================================================
# 7. 系统管理与审计相关表
# =====================================================

class SystemConfig(Base):
    """系统配置表"""
    __tablename__ = "system_configs"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    config_key = Column(String(100), unique=True, nullable=False)
    config_value = Column(Text, nullable=False)
    config_type = Column(String(20), default="string")
    description = Column(Text)
    category = Column(String(50))
    is_editable = Column(Boolean, default=True)
    created_at = Column(DateTime, default=func.current_timestamp())
    updated_at = Column(DateTime, default=func.current_timestamp())


class AuditLog(Base):
    """操作审计日志表"""
    __tablename__ = "audit_logs"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"))
    action = Column(String(50), nullable=False)
    entity_type = Column(String(50), nullable=False)
    entity_id = Column(Integer)
    old_values = Column(JSON)
    new_values = Column(JSON)
    ip_address = Column(String(45))
    user_agent = Column(Text)
    session_id = Column(String(255))
    _metadata = Column(JSON)
    created_at = Column(DateTime, default=func.current_timestamp())


class AppLog(Base):
    """应用日志表"""
    __tablename__ = "app_logs"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    log_level = Column(String(10), nullable=False)
    source = Column(String(50), nullable=False)
    message = Column(Text, nullable=False)
    details = Column(JSON)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"))
    request_id = Column(String(100))
    created_at = Column(DateTime, default=func.current_timestamp())


# =====================================================
# 8. 通知相关表
# =====================================================

class Notification(Base):
    """通知表"""
    __tablename__ = "notifications"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    notification_type = Column(String(30), nullable=False)
    title = Column(String(200), nullable=False)
    content = Column(Text, nullable=False)
    action_url = Column(Text)
    action_type = Column(String(50))
    related_entity_type = Column(String(50))
    related_entity_id = Column(Integer)
    priority = Column(String(10), default=Priority.MEDIUM.value)
    is_read = Column(Boolean, default=False)
    read_at = Column(DateTime)
    is_sent = Column(Boolean, default=False)
    sent_at = Column(DateTime)
    send_channel = Column(String(20))
    expires_at = Column(DateTime)
    created_at = Column(DateTime, default=func.current_timestamp())
    
    # 关系定义
    user = relationship("User", back_populates="notifications")
