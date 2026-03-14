"""Subscription management API endpoints."""

from datetime import datetime, timedelta
from typing import Any
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status, Header
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_active_user
from app.core.security import generate_api_key
from app.db.session import get_db
from app.models.user import User, SubscriptionTier
from app.models.subscription import Subscription, SubscriptionStatus
from app.schemas.subscription import (
    SubscriptionResponse,
    SubscriptionTier as TierSchema,
    CheckoutRequest,
    CheckoutResponse,
    UsageResponse,
)

router = APIRouter()


# Subscription tiers configuration
TIERS = {
    "free": TierSchema(
        id="free",
        name="Free",
        price=0,
        interval="month",
        websites_limit=1,
        scans_limit=5,
        features=[
            "1 website",
            "5 scans per month",
            "Basic accessibility reports",
            "Community support",
        ],
    ),
    "starter": TierSchema(
        id="starter",
        name="Starter",
        price=49,
        interval="month",
        websites_limit=3,
        scans_limit=-1,  # unlimited
        features=[
            "3 websites",
            "Unlimited scans",
            "WordPress plugin",
            "Email support",
            "Priority scanning",
            "AI-powered fix suggestions",
        ],
    ),
    "pro": TierSchema(
        id="pro",
        name="Pro",
        price=99,
        interval="month",
        websites_limit=10,
        scans_limit=-1,
        features=[
            "10 websites",
            "Unlimited scans",
            "All CMS integrations",
            "Priority support",
            "Advanced reporting",
            "API access",
            "Team collaboration",
        ],
    ),
    "agency": TierSchema(
        id="agency",
        name="Agency",
        price=249,
        interval="month",
        websites_limit=-1,
        scans_limit=-1,
        features=[
            "Unlimited websites",
            "Unlimited scans",
            "White-label reports",
            "Dedicated support",
            "Custom integrations",
            "SLA guarantee",
            "API access + webhooks",
        ],
    ),
}


@router.get("/tiers", response_model=list[TierSchema])
async def list_tiers() -> Any:
    """List available subscription tiers."""
    return list(TIERS.values())


@router.get("/subscription", response_model=SubscriptionResponse)
async def get_subscription(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """Get current user's subscription."""
    result = await db.execute(
        select(Subscription).where(Subscription.user_id == current_user.id)
    )
    subscription = result.scalar_one_or_none()

    if not subscription:
        # Create a default free subscription
        subscription = Subscription(
            user_id=current_user.id,
            tier=SubscriptionTier.FREE,
            status=SubscriptionStatus.ACTIVE,
        )
        db.add(subscription)
        await db.commit()
        await db.refresh(subscription)

    return SubscriptionResponse.model_validate(subscription)


@router.post("/checkout", response_model=CheckoutResponse)
async def create_checkout_session(
    checkout_data: CheckoutRequest,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """Create a Stripe checkout session for subscription upgrade."""
    from app.config import get_settings
    import stripe

    settings = get_settings()

    if not settings.stripe_secret_key:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Payment processing is not configured",
        )

    # Get price ID for the requested tier
    price_map = {
        "starter": settings.stripe_price_id_starter,
        "pro": settings.stripe_price_id_pro,
        "agency": settings.stripe_price_id_agency,
    }

    price_id = price_map.get(checkout_data.tier)
    if not price_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid subscription tier",
        )

    stripe.api_key = settings.stripe_secret_key

    # Get or create Stripe customer
    if current_user.stripe_customer_id:
        customer_id = current_user.stripe_customer_id
    else:
        customer = stripe.Customer.create(
            email=current_user.email,
            name=current_user.name,
        )
        customer_id = customer.id
        current_user.stripe_customer_id = customer_id
        await db.commit()

    # Create checkout session
    try:
        session = stripe.checkout.Session.create(
            customer=customer_id,
            payment_method_types=["card"],
            line_items=[
                {
                    "price": price_id,
                    "quantity": 1,
                }
            ],
            mode="subscription",
            success_url=checkout_data.success_url or f"{settings.frontend_url}/dashboard?checkout=success",
            cancel_url=checkout_data.cancel_url or f"{settings.frontend_url}/dashboard?checkout=cancelled",
            metadata={"user_id": str(current_user.id), "tier": checkout_data.tier},
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create checkout session: {str(e)}",
        )

    return CheckoutResponse(
        checkout_url=session.url,
        session_id=session.id,
    )


@router.post("/portal")
async def create_customer_portal_session(
    current_user: User = Depends(get_current_active_user),
) -> Any:
    """Create a Stripe customer portal session."""
    from app.config import get_settings
    import stripe

    settings = get_settings()

    if not current_user.stripe_customer_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No subscription found",
        )

    stripe.api_key = settings.stripe_secret_key

    try:
        session = stripe.billing_portal.Session.create(
            customer=current_user.stripe_customer_id,
            return_url=f"{settings.frontend_url}/dashboard",
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create portal session: {str(e)}",
        )

    return {"portal_url": session.url}


@router.post("/webhook/stripe")
async def stripe_webhook(
    raw_body: bytes,
    stripe_signature: str = Header(..., alias="Stripe-Signature"),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Handle Stripe webhook events."""
    from app.config import get_settings
    import stripe

    settings = get_settings()

    if not settings.stripe_webhook_secret:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Webhook secret not configured",
        )

    try:
        event = stripe.Webhook.construct_event(
            raw_body, stripe_signature, settings.stripe_webhook_secret
        )
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid payload",
        )
    except stripe.error.SignatureVerificationError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid signature",
        )

    # Handle the event
    if event["type"] == "checkout.session.completed":
        session = event["data"]["object"]
        await handle_checkout_completed(session, db)
    elif event["type"] == "customer.subscription.updated":
        subscription = event["data"]["object"]
        await handle_subscription_updated(subscription, db)
    elif event["type"] == "customer.subscription.deleted":
        subscription = event["data"]["object"]
        await handle_subscription_deleted(subscription, db)

    return {"status": "processed"}


async def handle_checkout_completed(session: dict, db: AsyncSession) -> None:
    """Handle successful checkout completion."""
    user_id = session.get("metadata", {}).get("user_id")
    tier = session.get("metadata", {}).get("tier", "starter")

    if not user_id:
        return

    from app.models.user import User
    from app.models.subscription import Subscription, SubscriptionStatus

    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()

    if not user:
        return

    # Update or create subscription
    result = await db.execute(
        select(Subscription).where(Subscription.user_id == user.id)
    )
    subscription = result.scalar_one_or_none()

    if subscription:
        subscription.tier = tier
        subscription.status = SubscriptionStatus.ACTIVE
        subscription.stripe_subscription_id = session.get("subscription")
    else:
        subscription = Subscription(
            user_id=user.id,
            tier=tier,
            status=SubscriptionStatus.ACTIVE,
            stripe_subscription_id=session.get("subscription"),
        )
        db.add(subscription)

    await db.commit()


async def handle_subscription_updated(subscription_data: dict, db: AsyncSession) -> None:
    """Handle subscription updates from Stripe."""
    stripe_sub_id = subscription_data.get("id")
    status = subscription_data.get("status")

    result = await db.execute(
        select(Subscription).where(Subscription.stripe_subscription_id == stripe_sub_id)
    )
    subscription = result.scalar_one_or_none()

    if not subscription:
        return

    # Map Stripe status to our status
    status_map = {
        "active": SubscriptionStatus.ACTIVE,
        "past_due": SubscriptionStatus.PAST_DUE,
        "canceled": SubscriptionStatus.CANCELED,
        "trialing": SubscriptionStatus.TRIALING,
        "incomplete": SubscriptionStatus.INCOMPLETE,
    }

    subscription.status = status_map.get(status, SubscriptionStatus.INCOMPLETE)
    subscription.cancel_at_period_end = subscription_data.get("cancel_at_period_end", False)

    await db.commit()


async def handle_subscription_deleted(subscription_data: dict, db: AsyncSession) -> None:
    """Handle subscription deletion from Stripe."""
    stripe_sub_id = subscription_data.get("id")

    result = await db.execute(
        select(Subscription).where(Subscription.stripe_subscription_id == stripe_sub_id)
    )
    subscription = result.scalar_one_or_none()

    if not subscription:
        return

    subscription.status = SubscriptionStatus.CANCELED
    subscription.tier = "free"

    await db.commit()


@router.get("/usage", response_model=UsageResponse)
async def get_usage(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """Get current usage statistics."""
    from app.models.website import Website
    from app.models.usage import UsageEvent, EventType
    from datetime import datetime, timedelta
    from sqlalchemy import select, func

    # Get limits
    limits = current_user.get_limits()

    # Count websites
    websites_result = await db.execute(
        select(func.count(Website.id)).where(
            Website.user_id == current_user.id,
            Website.is_active == True,
        )
    )
    website_count = websites_result.scalar() or 0

    # Count scans this month
    month_start = datetime.utcnow().replace(day=1, hour=0, minute=0, second=0, microsecond=0)

    scans_result = await db.execute(
        select(func.count(UsageEvent.id)).where(
            UsageEvent.user_id == current_user.id,
            UsageEvent.event_type == EventType.SCAN,
            UsageEvent.timestamp >= month_start,
        )
    )
    scan_count = scans_result.scalar() or 0

    # Calculate remaining
    remaining_websites = (
        limits["websites"] - website_count if limits["websites"] != -1 else -1
    )
    remaining_scans = (
        limits["scans_per_month"] - scan_count if limits["scans_per_month"] != -1 else -1
    )

    return UsageResponse(
        current_month={
            "websites": website_count,
            "scans": scan_count,
        },
        limits=limits,
        remaining={
            "websites": remaining_websites,
            "scans": remaining_scans,
        },
        reset_date=(month_start + timedelta(days=32)).replace(day=1),
    )
