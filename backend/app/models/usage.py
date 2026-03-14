"""Usage tracking model."""

import enum
from datetime import datetime
from typing import Optional

from sqlalchemy import String, DateTime, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, UUIDMixin, TimestampMixin


class EventType(str, enum.Enum):
    """Types of usage events for billing."""

    SCAN = "scan"
    API_CALL = "api_call"
    FIX_APPLIED = "fix_applied"
    REPORT_GENERATED = "report_generated"


class UsageEvent(Base, UUIDMixin, TimestampMixin):
    """Usage event for tracking and billing."""

    user_id: Mapped[str] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    event_type: Mapped[EventType] = mapped_column(String(100), nullable=False, index=True)
    resource_id: Mapped[Optional[str]] = mapped_column(String(100))  # scan_id, issue_id, etc.

    # Relationships
    user = relationship("User", back_populates="usage_events")
