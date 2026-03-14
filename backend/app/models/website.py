"""Website model."""

import enum
from datetime import datetime
from typing import Optional

from sqlalchemy import String, Boolean, DateTime, ForeignKey, Integer
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, UUIDMixin, TimestampMixin


class Platform(str, enum.Enum):
    """Website platforms."""

    GENERIC = "generic"
    WORDPRESS = "wordpress"
    SHOPIFY = "shopify"
    WEBFLOW = "webflow"
    SQUARESPACE = "squarespace"
    WIX = "wix"


class Website(Base, UUIDMixin, TimestampMixin):
    """Website model for sites being monitored."""

    user_id: Mapped[str] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    url: Mapped[str] = mapped_column(String(500), nullable=False)
    name: Mapped[Optional[str]] = mapped_column(String(255))
    platform: Mapped[Platform] = mapped_column(
        String(50), default=Platform.GENERIC, nullable=False
    )
    api_key: Mapped[Optional[str]] = mapped_column(String(100), unique=True, index=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    last_scan_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    latest_score: Mapped[Optional[int]] = mapped_column(Integer, default=None)

    # Relationships
    user = relationship("User", back_populates="websites")
    scans = relationship("Scan", back_populates="website", cascade="all, delete-orphan")

    def get_base_url(self) -> str:
        """Get normalized base URL."""
        from urllib.parse import urlparse

        parsed = urlparse(self.url)
        return f"{parsed.scheme}://{parsed.netloc}"
