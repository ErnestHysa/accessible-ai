"""Subscription model."""

import enum
from datetime import datetime
from typing import Optional

from sqlalchemy import String, DateTime, ForeignKey, Boolean
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, UUIDMixin, TimestampMixin


class SubscriptionStatus(str, enum.Enum):
    """Subscription statuses."""

    ACTIVE = "active"
    CANCELED = "canceled"
    PAST_DUE = "past_due"
    TRIALING = "trialing"
    INCOMPLETE = "incomplete"


class Subscription(Base, UUIDMixin, TimestampMixin):
    """User subscription model."""

    user_id: Mapped[str] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False, unique=True, index=True
    )
    stripe_subscription_id: Mapped[Optional[str]] = mapped_column(
        String(255), unique=True, index=True
    )
    tier: Mapped[str] = mapped_column(String(50), nullable=False)  # free, starter, pro, agency
    status: Mapped[SubscriptionStatus] = mapped_column(
        String(50), default=SubscriptionStatus.INCOMPLETE, nullable=False
    )

    current_period_start: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    current_period_end: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    cancel_at_period_end: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    trial_start: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    trial_end: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))

    # Relationships
    user = relationship("User", back_populates="subscription")

    @property
    def is_active(self) -> bool:
        """Check if subscription is active."""
        return self.status == SubscriptionStatus.ACTIVE or self.status == SubscriptionStatus.TRIALING

    @property
    def is_trialing(self) -> bool:
        """Check if subscription is in trial period."""
        return self.status == SubscriptionStatus.TRIALING
