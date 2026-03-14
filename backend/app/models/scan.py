"""Scan and Issue models."""

import enum
from datetime import datetime
from typing import Optional

from sqlalchemy import String, Integer, DateTime, ForeignKey, Text, Boolean
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, UUIDMixin, TimestampMixin


class ScanStatus(str, enum.Enum):
    """Scan statuses."""

    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class Severity(str, enum.Enum):
    """Issue severity levels."""

    CRITICAL = "critical"
    SERIOUS = "serious"
    MODERATE = "moderate"
    MINOR = "minor"


class Scan(Base, UUIDMixin, TimestampMixin):
    """Accessibility scan model."""

    website_id: Mapped[str] = mapped_column(
        ForeignKey("websites.id", ondelete="CASCADE"), nullable=False, index=True
    )
    status: Mapped[ScanStatus] = mapped_column(
        String(50), default=ScanStatus.PENDING, nullable=False, index=True
    )
    score: Mapped[Optional[int]] = mapped_column(Integer, default=None)
    total_issues: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    critical_issues: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    serious_issues: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    moderate_issues: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    minor_issues: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    started_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    report_url: Mapped[Optional[str]] = mapped_column(String(500))
    error_message: Mapped[Optional[str]] = mapped_column(Text)

    # Relationships
    website = relationship("Website", back_populates="scans")
    issues = relationship("Issue", back_populates="scan", cascade="all, delete-orphan")

    def calculate_score(self) -> int:
        """Calculate accessibility score (0-100)."""
        if self.total_issues == 0:
            return 100

        # Weight issues by severity
        weights = {
            Severity.CRITICAL: 20,
            Severity.SERIOUS: 10,
            Severity.MODERATE: 5,
            Severity.MINOR: 1,
        }

        penalty = (
            self.critical_issues * weights[Severity.CRITICAL]
            + self.serious_issues * weights[Severity.SERIOUS]
            + self.moderate_issues * weights[Severity.MODERATE]
            + self.minor_issues * weights[Severity.MINOR]
        )

        score = max(0, 100 - penalty)
        return score


class Issue(Base, UUIDMixin, TimestampMixin):
    """Accessibility issue model."""

    scan_id: Mapped[str] = mapped_column(
        ForeignKey("scans.id", ondelete="CASCADE"), nullable=False, index=True
    )
    type: Mapped[str] = mapped_column(String(100), nullable=False, index=True)  # WCAG rule ID
    severity: Mapped[Severity] = mapped_column(String(20), nullable=False, index=True)
    selector: Mapped[Optional[str]] = mapped_column(String(500))  # CSS selector

    description: Mapped[str] = mapped_column(Text, nullable=False)
    impact: Mapped[Optional[str]] = mapped_column(Text)

    fix_suggestion: Mapped[Optional[str]] = mapped_column(Text)
    fix_code: Mapped[Optional[str]] = mapped_column(Text)  # AI-generated fix

    is_fixed: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    # Additional context
    page_url: Mapped[Optional[str]] = mapped_column(String(500))
    element_html: Mapped[Optional[str]] = mapped_column(Text)

    # Relationships
    scan = relationship("Scan", back_populates="issues")
