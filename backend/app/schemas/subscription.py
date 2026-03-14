"""Subscription schemas."""

from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field


class SubscriptionTier(BaseModel):
    """Subscription tier information."""

    id: str
    name: str
    price: int
    interval: str
    websites_limit: int
    scans_limit: int  # -1 for unlimited
    features: list[str]


class SubscriptionResponse(BaseModel):
    """User subscription response."""

    id: UUID
    tier: str
    status: str
    current_period_start: Optional[datetime] = None
    current_period_end: Optional[datetime] = None
    cancel_at_period_end: bool = False
    trial_end: Optional[datetime] = None

    class Config:
        from_attributes = True


class CheckoutRequest(BaseModel):
    """Checkout session request."""

    tier: str = Field(..., pattern="^(starter|pro|agency)$")
    success_url: Optional[str] = None
    cancel_url: Optional[str] = None


class CheckoutResponse(BaseModel):
    """Checkout session response."""

    checkout_url: str
    session_id: str


class UsageResponse(BaseModel):
    """Usage statistics response."""

    current_month: dict
    limits: dict
    remaining: dict
    reset_date: datetime
