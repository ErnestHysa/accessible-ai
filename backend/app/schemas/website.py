"""Website schemas."""

from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, HttpUrl, Field


class WebsiteBase(BaseModel):
    """Base website schema."""

    url: HttpUrl
    name: Optional[str] = Field(None, max_length=255)
    platform: str = Field("generic", pattern="^(generic|wordpress|shopify|webflow|squarespace|wix)$")


class WebsiteCreate(WebsiteBase):
    """Website creation schema."""

    pass


class WebsiteUpdate(BaseModel):
    """Website update schema."""

    name: Optional[str] = Field(None, max_length=255)
    platform: Optional[str] = Field(None, pattern="^(generic|wordpress|shopify|webflow|squarespace|wix)$")
    is_active: Optional[bool] = None


class WebsiteResponse(WebsiteBase):
    """Website response schema."""

    id: UUID
    user_id: UUID
    api_key: Optional[str] = None
    is_active: bool
    last_scan_at: Optional[datetime] = None
    latest_score: Optional[int] = None
    created_at: datetime

    class Config:
        from_attributes = True


class ScanTrigger(BaseModel):
    """Schema to trigger a scan."""

    full_scan: bool = Field(default=False, description="Scan all pages or just homepage")
    max_pages: int = Field(default=10, ge=1, le=100, description="Maximum pages to scan")
