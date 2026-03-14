"""Scan schemas."""

from datetime import datetime
from typing import Optional, List
from uuid import UUID
from enum import Enum

from pydantic import BaseModel, Field


class ScanStatus(str, Enum):
    """Scan status enum."""

    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class Severity(str, Enum):
    """Issue severity enum."""

    CRITICAL = "critical"
    SERIOUS = "serious"
    MODERATE = "moderate"
    MINOR = "minor"


class ScanResponse(BaseModel):
    """Scan response schema."""

    id: UUID
    website_id: UUID
    status: ScanStatus
    score: Optional[int] = None
    total_issues: int
    critical_issues: int
    serious_issues: int
    moderate_issues: int
    minor_issues: int
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    report_url: Optional[str] = None
    error_message: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


class IssueResponse(BaseModel):
    """Issue response schema."""

    id: UUID
    scan_id: UUID
    type: str
    severity: Severity
    selector: Optional[str] = None
    description: str
    impact: Optional[str] = None
    fix_suggestion: Optional[str] = None
    fix_code: Optional[str] = None
    is_fixed: bool
    page_url: Optional[str] = None
    element_html: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


class IssueFixRequest(BaseModel):
    """Schema to apply a fix."""

    auto_apply: bool = Field(default=False, description="Automatically apply the fix if possible")


class IssueFixResponse(BaseModel):
    """Response for fix application."""

    success: bool
    message: str
    fix_applied: bool
    fix_code: Optional[str] = None


class ScanSummary(BaseModel):
    """Summary of scan results."""

    scan_id: UUID
    score: int
    total_issues: int
    issues_by_severity: dict
    top_issues: List[IssueResponse]
