"""Scan API endpoints."""

from typing import Any, List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.dependencies import get_current_active_user
from app.db.session import get_db
from app.models.user import User
from app.models.scan import Scan, Issue, Severity
from app.schemas.scan import ScanResponse, IssueResponse, IssueFixRequest, IssueFixResponse

router = APIRouter()


@router.get("", response_model=List[ScanResponse])
async def list_scans(
    website_id: UUID = None,
    limit: int = Query(10, ge=1, le=100),
    offset: int = Query(0, ge=0),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """List scans, optionally filtered by website."""
    query = (
        select(Scan)
        .join(Website, Scan.website_id == Website.id)
        .where(Website.user_id == current_user.id)
        .order_by(Scan.created_at.desc())
    )

    if website_id:
        query = query.where(Scan.website_id == website_id)

    query = query.limit(limit).offset(offset)

    result = await db.execute(query)
    scans = result.scalars().all()

    return [ScanResponse.model_validate(s) for s in scans]


@router.get("/{scan_id}", response_model=ScanResponse)
async def get_scan(
    scan_id: UUID,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """Get details of a specific scan."""
    result = await db.execute(
        select(Scan)
        .join(Website, Scan.website_id == Website.id)
        .where(
            Scan.id == scan_id,
            Website.user_id == current_user.id,
        )
        .options(selectinload(Scan.issues))
    )
    scan = result.scalar_one_or_none()

    if not scan:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Scan not found",
        )

    return ScanResponse.model_validate(scan)


@router.get("/{scan_id}/issues", response_model=List[IssueResponse])
async def get_scan_issues(
    scan_id: UUID,
    severity: Severity = None,
    is_fixed: bool = None,
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """Get issues for a scan, with optional filtering."""
    # First verify user owns this scan
    scan_result = await db.execute(
        select(Scan)
        .join(Website, Scan.website_id == Website.id)
        .where(
            Scan.id == scan_id,
            Website.user_id == current_user.id,
        )
    )
    scan = scan_result.scalar_one_or_none()

    if not scan:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Scan not found",
        )

    # Get issues
    query = select(Issue).where(Issue.scan_id == scan_id)

    if severity:
        query = query.where(Issue.severity == severity)
    if is_fixed is not None:
        query = query.where(Issue.is_fixed == is_fixed)

    query = query.order_by(Issue.created_at.desc()).limit(limit).offset(offset)

    result = await db.execute(query)
    issues = result.scalars().all()

    return [IssueResponse.model_validate(i) for i in issues]


@router.get("/issues/{issue_id}", response_model=IssueResponse)
async def get_issue(
    issue_id: UUID,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """Get details of a specific issue."""
    result = await db.execute(
        select(Issue)
        .join(Scan, Issue.scan_id == Scan.id)
        .join(Website, Scan.website_id == Website.id)
        .where(
            Issue.id == issue_id,
            Website.user_id == current_user.id,
        )
    )
    issue = result.scalar_one_or_none()

    if not issue:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Issue not found",
        )

    return IssueResponse.model_validate(issue)


@router.post("/issues/{issue_id}/fix", response_model=IssueFixResponse)
async def apply_fix(
    issue_id: UUID,
    fix_request: IssueFixRequest,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """Get or apply a fix for an issue."""
    result = await db.execute(
        select(Issue)
        .join(Scan, Issue.scan_id == Scan.id)
        .join(Website, Scan.website_id == Website.id)
        .where(
            Issue.id == issue_id,
            Website.user_id == current_user.id,
        )
    )
    issue = result.scalar_one_or_none()

    if not issue:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Issue not found",
        )

    # If AI fix hasn't been generated yet, generate it
    if not issue.fix_code:
        from app.services.ai_fixer import generate_fix

        issue.fix_code = await generate_fix(issue)
        await db.commit()

    # For WordPress/plugin integrations, auto-apply might be possible
    fix_applied = False
    message = "Fix code generated"

    if fix_request.auto_apply:
        # Check if website has plugin integration
        scan_result = await db.execute(
            select(Scan).where(Scan.id == issue.scan_id).options(selectinload(Scan.website))
        )
        scan = scan_result.scalar_one_or_none()

        if scan and scan.website.platform == "wordpress":
            # In a real implementation, this would call the WordPress API
            # For MVP, we'll just mark it as could be applied
            message = "Auto-apply available for WordPress sites via plugin"
            fix_applied = False  # Would be True if successfully applied
        else:
            message = "Auto-apply requires WordPress plugin or manual implementation"

    return IssueFixResponse(
        success=True,
        message=message,
        fix_applied=fix_applied,
        fix_code=issue.fix_code,
    )
