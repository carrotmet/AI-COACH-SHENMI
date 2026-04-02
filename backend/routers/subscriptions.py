# -*- coding: utf-8 -*-
"""
深觅 AI Coach - 订阅路由模块

该模块提供订阅管理相关的API接口：
- GET /subscriptions/plans - 获取订阅计划
- GET /subscriptions/me - 获取当前订阅
- POST /subscriptions/subscribe - 订阅
"""

from typing import Optional, List
from datetime import datetime, date, timedelta

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc, and_

from database.connection import get_db_session
from database.models import (
    User,
    Subscription,
    Payment,
    UsageQuota,
    SubscriptionType,
    SubscriptionStatus,
    BillingCycle,
    PaymentStatus,
    PaymentType,
)
from middleware.auth_middleware import get_current_user
from utils.response import (
    success_response,
    error_response,
    ResponseCode,
    ApiResponse,
)


# =====================================================
# 路由定义
# =====================================================
router = APIRouter(
    tags=["订阅管理"],
    dependencies=[Depends(get_current_user)],
    responses={
        401: {"description": "未授权"},
        403: {"description": "无权限"},
    }
)


# =====================================================
# 订阅计划定义
# =====================================================

SUBSCRIPTION_PLANS = {
    "free": {
        "code": "free",
        "name": "免费版",
        "description": "免费体验基础功能",
        "price_monthly": 0,
        "price_yearly": 0,
        "currency": "CNY",
        "features": [
            "VIA优势测评（完整版）",
            "免费版测评报表（摘要）",
            "AI优势教练对话：3次/日",
            "对话历史保存：7天"
        ],
        "limits": {
            "daily_chat_limit": 3,
            "history_retention_days": 7,
            "monthly_assessment_limit": 1
        }
    },
    "basic": {
        "code": "basic",
        "name": "基础版",
        "description": "适合个人成长入门",
        "price_monthly": 29,
        "price_yearly": 290,
        "currency": "CNY",
        "features": [
            "包含免费版所有功能",
            "完整版测评报表（PDF下载）",
            "AI优势教练对话：20次/日",
            "对话历史保存：30天",
            "优先客服支持"
        ],
        "limits": {
            "daily_chat_limit": 20,
            "history_retention_days": 30,
            "monthly_assessment_limit": 3
        }
    },
    "premium": {
        "code": "premium",
        "name": "专业版",
        "description": "全方位个人成长支持",
        "price_monthly": 59,
        "price_yearly": 590,
        "currency": "CNY",
        "features": [
            "包含基础版所有功能",
            "AI优势教练对话：无限次数",
            "对话历史保存：永久",
            "专属成长计划",
            "优势发展练习库",
            "1对1教练咨询（每月1次）"
        ],
        "limits": {
            "daily_chat_limit": -1,  # 无限
            "history_retention_days": -1,  # 永久
            "monthly_assessment_limit": -1  # 无限
        }
    }
}


# =====================================================
# 请求模型
# =====================================================

class SubscribeRequest(BaseModel):
    """订阅请求"""
    plan_code: str = Field(..., description="套餐代码: free/basic/premium")
    billing_cycle: str = Field(default="monthly", description="计费周期: monthly/yearly")
    
    class Config:
        json_schema_extra = {
            "example": {
                "plan_code": "premium",
                "billing_cycle": "monthly"
            }
        }


class CancelSubscriptionRequest(BaseModel):
    """取消订阅请求"""
    reason: Optional[str] = Field(None, description="取消原因")
    
    class Config:
        json_schema_extra = {
            "example": {
                "reason": "暂时不需要了"
            }
        }


# =====================================================
# 响应模型
# =====================================================

class PlanFeature(BaseModel):
    """套餐功能"""
    daily_chat_limit: int = Field(..., description="每日对话限制")
    history_retention_days: int = Field(..., description="历史保存天数")
    monthly_assessment_limit: int = Field(..., description="每月测评限制")


class SubscriptionPlan(BaseModel):
    """订阅计划"""
    code: str = Field(..., description="套餐代码")
    name: str = Field(..., description="套餐名称")
    description: str = Field(..., description="套餐描述")
    price_monthly: float = Field(..., description="月付价格")
    price_yearly: float = Field(..., description="年付价格")
    currency: str = Field(..., description="货币单位")
    features: List[str] = Field(..., description="功能列表")
    limits: PlanFeature = Field(..., description="配额限制")


class CurrentSubscription(BaseModel):
    """当前订阅"""
    subscription_id: int = Field(..., description="订阅ID")
    plan_code: str = Field(..., description="套餐代码")
    plan_name: str = Field(..., description="套餐名称")
    status: str = Field(..., description="订阅状态")
    billing_cycle: str = Field(..., description="计费周期")
    price: float = Field(..., description="价格")
    currency: str = Field(..., description="货币")
    start_date: str = Field(..., description="开始日期")
    end_date: Optional[str] = Field(None, description="结束日期")
    auto_renew: bool = Field(..., description="是否自动续费")
    days_remaining: Optional[int] = Field(None, description="剩余天数")


class UsageQuotaInfo(BaseModel):
    """使用配额信息"""
    plan_type: str = Field(..., description="套餐类型")
    conversation_used: int = Field(..., description="已用对话数")
    conversation_limit: int = Field(..., description="对话限制")
    message_used: int = Field(..., description="已用消息数")
    message_limit: int = Field(..., description="消息限制")
    assessment_used: int = Field(..., description="已用测评数")
    assessment_limit: int = Field(..., description="测评限制")
    ai_call_used: int = Field(..., description="已用AI调用数")
    ai_call_limit: int = Field(..., description="AI调用限制")


class SubscriptionResult(BaseModel):
    """订阅结果"""
    subscription_id: int = Field(..., description="订阅ID")
    plan_code: str = Field(..., description="套餐代码")
    status: str = Field(..., description="状态")
    message: str = Field(..., description="结果消息")


class MessageResponse(BaseModel):
    """消息响应"""
    message: str = Field(..., description="操作结果消息")


# =====================================================
# 路由处理函数
# =====================================================

@router.get(
    "/plans",
    response_model=ApiResponse[List[SubscriptionPlan]],
    summary="获取订阅计划",
    description="获取所有可用的订阅计划列表"
)
async def get_subscription_plans(
    current_user: dict = Depends(get_current_user)
):
    """
    获取订阅计划列表
    
    返回所有可用的订阅套餐信息，包括价格、功能和配额限制
    """
    plans = []
    for code, plan in SUBSCRIPTION_PLANS.items():
        plans.append({
            "code": plan["code"],
            "name": plan["name"],
            "description": plan["description"],
            "price_monthly": plan["price_monthly"],
            "price_yearly": plan["price_yearly"],
            "currency": plan["currency"],
            "features": plan["features"],
            "limits": plan["limits"]
        })
    
    return success_response(data=plans)


@router.get(
    "/me",
    response_model=ApiResponse[CurrentSubscription],
    summary="获取当前订阅",
    description="获取当前用户的订阅信息和使用配额"
)
async def get_current_subscription(
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
):
    """
    获取当前订阅信息
    
    返回用户的当前订阅状态、套餐信息和使用配额
    """
    user_id = current_user["id"]
    
    # 获取最新订阅
    result = await db.execute(
        select(Subscription)
        .where(
            and_(
                Subscription.user_id == user_id,
                Subscription.status.in_(["active", "trial"])
            )
        )
        .order_by(desc(Subscription.created_at))
    )
    subscription = result.scalars().first()
    
    # 获取使用配额
    quota_result = await db.execute(
        select(UsageQuota).where(UsageQuota.user_id == user_id)
    )
    quota = quota_result.scalar_one_or_none()
    
    # 计算剩余天数
    days_remaining = None
    if subscription and subscription.end_date:
        days_remaining = (subscription.end_date - date.today()).days
        if days_remaining < 0:
            days_remaining = 0
    
    # 获取套餐名称
    plan_code = subscription.plan_type if subscription else "free"
    plan_name = SUBSCRIPTION_PLANS.get(plan_code, {}).get("name", "免费版")
    
    if not subscription:
        # 返回免费版信息
        return success_response(
            data={
                "subscription_id": None,
                "plan_code": "free",
                "plan_name": "免费版",
                "status": "active",
                "billing_cycle": "monthly",
                "price": 0,
                "currency": "CNY",
                "start_date": current_user.get("created_at"),
                "end_date": None,
                "auto_renew": False,
                "days_remaining": None,
                "usage_quota": {
                    "plan_type": "free",
                    "conversation_used": quota.conversation_used if quota else 0,
                    "conversation_limit": quota.conversation_limit if quota else 10,
                    "message_used": quota.message_used if quota else 0,
                    "message_limit": quota.message_limit if quota else 100,
                    "assessment_used": quota.assessment_used if quota else 0,
                    "assessment_limit": quota.assessment_limit if quota else 1,
                    "ai_call_used": quota.ai_call_used if quota else 0,
                    "ai_call_limit": quota.ai_call_limit if quota else 100
                } if quota else None
            }
        )
    
    return success_response(
        data={
            "subscription_id": subscription.id,
            "plan_code": subscription.plan_type,
            "plan_name": plan_name,
            "status": subscription.status,
            "billing_cycle": subscription.billing_cycle,
            "price": subscription.price,
            "currency": subscription.currency,
            "start_date": subscription.start_date.isoformat() if subscription.start_date else None,
            "end_date": subscription.end_date.isoformat() if subscription.end_date else None,
            "auto_renew": subscription.auto_renew,
            "days_remaining": days_remaining,
            "usage_quota": {
                "plan_type": quota.plan_type if quota else plan_code,
                "conversation_used": quota.conversation_used if quota else 0,
                "conversation_limit": quota.conversation_limit if quota else 10,
                "message_used": quota.message_used if quota else 0,
                "message_limit": quota.message_limit if quota else 100,
                "assessment_used": quota.assessment_used if quota else 0,
                "assessment_limit": quota.assessment_limit if quota else 1,
                "ai_call_used": quota.ai_call_used if quota else 0,
                "ai_call_limit": quota.ai_call_limit if quota else 100
            } if quota else None
        }
    )


@router.post(
    "/subscribe",
    response_model=ApiResponse[SubscriptionResult],
    summary="订阅套餐",
    description="订阅指定的套餐计划"
)
async def subscribe(
    request: SubscribeRequest,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
):
    """
    订阅套餐
    
    - **plan_code**: 套餐代码 (free/basic/premium)
    - **billing_cycle**: 计费周期 (monthly/yearly)
    
    订阅成功后返回订阅信息
    """
    user_id = current_user["id"]
    
    # 验证套餐代码
    if request.plan_code not in SUBSCRIPTION_PLANS:
        raise HTTPException(
            status_code=400,
            detail=error_response(
                code=ResponseCode.BAD_REQUEST,
                detail="无效的套餐代码"
            )
        )
    
    plan = SUBSCRIPTION_PLANS[request.plan_code]
    
    # 计算价格
    if request.billing_cycle == "yearly":
        price = plan["price_yearly"]
    else:
        price = plan["price_monthly"]
    
    # 免费套餐直接激活
    if request.plan_code == "free":
        # 更新用户订阅类型
        user_result = await db.execute(
            select(User).where(User.id == user_id)
        )
        user = user_result.scalar_one()
        user.subscription_type = SubscriptionType.FREE.value
        
        # 更新使用配额
        quota_result = await db.execute(
            select(UsageQuota).where(UsageQuota.user_id == user_id)
        )
        quota = quota_result.scalar_one_or_none()
        
        if quota:
            quota.plan_type = SubscriptionType.FREE.value
            quota.conversation_limit = plan["limits"]["daily_chat_limit"]
            quota.message_limit = 100
            quota.assessment_limit = plan["limits"]["monthly_assessment_limit"]
        
        await db.commit()
        
        return success_response(
            data={
                "subscription_id": None,
                "plan_code": request.plan_code,
                "status": "active",
                "message": "已切换到免费版"
            },
            message="订阅成功"
        )
    
    # 付费套餐创建订阅记录
    start_date = date.today()
    
    if request.billing_cycle == "yearly":
        end_date = start_date + timedelta(days=365)
    else:
        end_date = start_date + timedelta(days=30)
    
    subscription = Subscription(
        user_id=user_id,
        plan_type=request.plan_code,
        billing_cycle=request.billing_cycle,
        status=SubscriptionStatus.ACTIVE.value,
        price=price,
        currency=plan["currency"],
        start_date=start_date,
        end_date=end_date,
        auto_renew=True,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    
    db.add(subscription)
    await db.flush()
    
    # 创建支付记录
    payment = Payment(
        user_id=user_id,
        subscription_id=subscription.id,
        payment_type=PaymentType.SUBSCRIPTION.value,
        amount=price,
        currency=plan["currency"],
        status=PaymentStatus.COMPLETED.value,  # 模拟支付成功
        description=f"订阅{plan['name']} - {request.billing_cycle}",
        paid_at=datetime.utcnow(),
        created_at=datetime.utcnow()
    )
    
    db.add(payment)
    
    # 更新用户订阅类型
    user_result = await db.execute(
        select(User).where(User.id == user_id)
    )
    user = user_result.scalar_one()
    user.subscription_type = request.plan_code
    
    # 更新使用配额
    quota_result = await db.execute(
        select(UsageQuota).where(UsageQuota.user_id == user_id)
    )
    quota = quota_result.scalar_one_or_none()
    
    if quota:
        quota.plan_type = request.plan_code
        quota.conversation_limit = plan["limits"]["daily_chat_limit"]
        quota.message_limit = 1000 if request.plan_code == "basic" else 999999
        quota.assessment_limit = plan["limits"]["monthly_assessment_limit"]
    
    await db.commit()
    
    return success_response(
        data={
            "subscription_id": subscription.id,
            "plan_code": request.plan_code,
            "status": "active",
            "message": f"成功订阅{plan['name']}"
        },
        message="订阅成功"
    )


@router.post(
    "/cancel",
    response_model=ApiResponse[MessageResponse],
    summary="取消订阅",
    description="取消当前订阅的自动续费"
)
async def cancel_subscription(
    request: CancelSubscriptionRequest,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
):
    """
    取消订阅
    
    - **reason**: 取消原因（可选）
    
    取消后当前订阅将在到期后失效
    """
    user_id = current_user["id"]
    
    # 获取当前订阅
    result = await db.execute(
        select(Subscription)
        .where(
            and_(
                Subscription.user_id == user_id,
                Subscription.status == SubscriptionStatus.ACTIVE.value
            )
        )
        .order_by(desc(Subscription.created_at))
    )
    subscription = result.scalars().first()
    
    if not subscription:
        raise HTTPException(
            status_code=400,
            detail=error_response(
                code=ResponseCode.BAD_REQUEST,
                detail="当前没有活跃的订阅"
            )
        )
    
    # 更新订阅状态
    subscription.auto_renew = False
    subscription.cancellation_reason = request.reason
    subscription.cancelled_at = datetime.utcnow()
    subscription.updated_at = datetime.utcnow()
    
    await db.commit()
    
    return success_response(
        data={"message": "订阅已取消，当前套餐将在到期后失效"}
    )


@router.get(
    "/usage",
    response_model=ApiResponse[UsageQuotaInfo],
    summary="获取使用配额",
    description="获取当前用户的使用配额和用量统计"
)
async def get_usage_quota(
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
):
    """
    获取使用配额
    
    返回用户的各项服务使用配额和已用量
    """
    user_id = current_user["id"]
    
    # 获取使用配额
    result = await db.execute(
        select(UsageQuota).where(UsageQuota.user_id == user_id)
    )
    quota = result.scalar_one_or_none()
    
    if not quota:
        # 返回默认配额
        return success_response(
            data={
                "plan_type": "free",
                "conversation_used": 0,
                "conversation_limit": 10,
                "message_used": 0,
                "message_limit": 100,
                "assessment_used": 0,
                "assessment_limit": 1,
                "ai_call_used": 0,
                "ai_call_limit": 100
            }
        )
    
    return success_response(
        data={
            "plan_type": quota.plan_type,
            "conversation_used": quota.conversation_used,
            "conversation_limit": quota.conversation_limit,
            "message_used": quota.message_used,
            "message_limit": quota.message_limit,
            "assessment_used": quota.assessment_used,
            "assessment_limit": quota.assessment_limit,
            "ai_call_used": quota.ai_call_used,
            "ai_call_limit": quota.ai_call_limit
        }
    )


@router.get(
    "/history",
    response_model=ApiResponse[dict],
    summary="获取订阅历史",
    description="获取用户的订阅历史记录"
)
async def get_subscription_history(
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
):
    """
    获取订阅历史
    
    返回用户的所有订阅记录
    """
    user_id = current_user["id"]
    
    # 获取订阅历史
    result = await db.execute(
        select(Subscription)
        .where(Subscription.user_id == user_id)
        .order_by(desc(Subscription.created_at))
    )
    subscriptions = result.scalars().all()
    
    items = []
    for sub in subscriptions:
        plan_name = SUBSCRIPTION_PLANS.get(sub.plan_type, {}).get("name", sub.plan_type)
        items.append({
            "subscription_id": sub.id,
            "plan_code": sub.plan_type,
            "plan_name": plan_name,
            "status": sub.status,
            "billing_cycle": sub.billing_cycle,
            "price": sub.price,
            "currency": sub.currency,
            "start_date": sub.start_date.isoformat() if sub.start_date else None,
            "end_date": sub.end_date.isoformat() if sub.end_date else None,
            "auto_renew": sub.auto_renew,
            "cancelled_at": sub.cancelled_at.isoformat() if sub.cancelled_at else None,
            "created_at": sub.created_at.isoformat() if sub.created_at else None
        })
    
    return success_response(
        data={
            "items": items,
            "total": len(items)
        }
    )
