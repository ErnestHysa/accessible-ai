"""User model."""

import enum
from datetime import datetime
from typing import Optional

from sqlalchemy import String, Boolean, DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, UUIDMixin, TimestampMixin


class SubscriptionTier(str, enum.Enum):
    """Subscription tiers."""

    FREE = "free"
    STARTER = "starter"
    PRO = "pro"
    AGENCY = "agency"


class User(Base, UUIDMixin, TimestampMixin):
    """User model."""

    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    name: Mapped[Optional[str]] = mapped_column(String(255))
    subscription_tier: Mapped[SubscriptionTier] = mapped_column(
        String(50), default=SubscriptionTier.FREE, nullable=False
    )
    stripe_customer_id: Mapped[Optional[str]] = mapped_column(String(255))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    email_verified: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    # Relationships
    websites = relationship("Website", back_populates="user", cascade="all, delete-orphan")
    subscription = relationship(
        "Subscription", back_populates="user", uselist=False, cascade="all, delete-orphan"
    )
    usage_events = relationship("UsageEvent", back_populates="user", cascade="all, delete-orphan")

    def get_limits(self) -> dict:
        """Get subscription limits for this user."""
        from app.config import get_settings

        settings = get_settings()
        return settings.limits.get(self.subscription_tier, settings.limits["free"])

    @property
    def is_paid(self) -> bool:
        """Check if user has paid subscription."""
        return self.subscription_tier != SubscriptionTier.FREE
