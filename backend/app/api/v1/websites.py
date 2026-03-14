"""Website management API endpoints."""

from typing import Any, List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_active_user, get_paid_user
from app.core.security import generate_api_key
from app.db.session import get_db
from app.models.user import User
from app.models.website import Website
from app.models.scan import Scan
from app.schemas.website import WebsiteCreate, WebsiteUpdate, WebsiteResponse, ScanTrigger

router = APIRouter()


@router.post("", response_model=WebsiteResponse, status_code=status.HTTP_201_CREATED)
async def create_website(
    website_data: WebsiteCreate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """Add a new website to monitor."""
    # Check user's subscription limits
    limits = current_user.get_limits()

    if limits["websites"] != -1:  # -1 means unlimited
        # Count existing websites
        result = await db.execute(
            func.count(Website.id).where(Website.user_id == current_user.id, Website.is_active == True)
        )
        website_count = result.scalar() or 0

        if website_count >= limits["websites"]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"You've reached your limit of {limits['websites']} website(s). Upgrade your subscription to add more.",
            )

    # Check if URL already exists for this user
    normalized_url = str(website_data.url).rstrip("/")
    result = await db.execute(
        select(Website).where(
            Website.user_id == current_user.id,
            Website.url == normalized_url,
        )
    )
    existing = result.scalar_one_or_none()

    if existing:
        # Return existing website
        return WebsiteResponse.model_validate(existing)

    # Create new website
    website = Website(
        user_id=current_user.id,
        url=normalized_url,
        name=website_data.name,
        platform=website_data.platform,
        api_key=generate_api_key(),
    )

    db.add(website)
    await db.commit()
    await db.refresh(website)

    return WebsiteResponse.model_validate(website)


@router.get("", response_model=List[WebsiteResponse])
async def list_websites(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """List all websites for the current user."""
    result = await db.execute(
        select(Website)
        .where(Website.user_id == current_user.id)
        .order_by(Website.created_at.desc())
    )
    websites = result.scalars().all()

    return [WebsiteResponse.model_validate(w) for w in websites]


@router.get("/{website_id}", response_model=WebsiteResponse)
async def get_website(
    website_id: UUID,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """Get details of a specific website."""
    result = await db.execute(
        select(Website).where(
            Website.id == website_id,
            Website.user_id == current_user.id,
        )
    )
    website = result.scalar_one_or_none()

    if not website:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Website not found",
        )

    return WebsiteResponse.model_validate(website)


@router.put("/{website_id}", response_model=WebsiteResponse)
async def update_website(
    website_id: UUID,
    website_data: WebsiteUpdate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """Update website details."""
    result = await db.execute(
        select(Website).where(
            Website.id == website_id,
            Website.user_id == current_user.id,
        )
    )
    website = result.scalar_one_or_none()

    if not website:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Website not found",
        )

    # Update fields
    if website_data.name is not None:
        website.name = website_data.name
    if website_data.platform is not None:
        website.platform = website_data.platform
    if website_data.is_active is not None:
        website.is_active = website_data.is_active

    await db.commit()
    await db.refresh(website)

    return WebsiteResponse.model_validate(website)


@router.delete("/{website_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_website(
    website_id: UUID,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> None:
    """Delete a website."""
    result = await db.execute(
        select(Website).where(
            Website.id == website_id,
            Website.user_id == current_user.id,
        )
    )
    website = result.scalar_one_or_none()

    if not website:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Website not found",
        )

    await db.delete(website)
    await db.commit()


@router.post("/{website_id}/scan", response_model=dict)
async def trigger_scan(
    website_id: UUID,
    scan_options: ScanTrigger = ScanTrigger(),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """Trigger an accessibility scan for a website."""
    # Verify website exists and belongs to user
    result = await db.execute(
        select(Website).where(
            Website.id == website_id,
            Website.user_id == current_user.id,
        )
    )
    website = result.scalar_one_or_none()

    if not website:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Website not found",
        )

    # Check scan limits
    limits = current_user.get_limits()

    if limits["scans_per_month"] != -1:
        # Count scans this month
        from datetime import datetime
        from app.models.usage import UsageEvent, EventType

        result = await db.execute(
            select(func.count(UsageEvent.id))
            .where(UsageEvent.user_id == current_user.id)
            .where(UsageEvent.event_type == EventType.SCAN)
        )
        scan_count = result.scalar() or 0

        if scan_count >= limits["scans_per_month"]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"You've reached your monthly limit of {limits['scans_per_month']} scan(s). Upgrade your subscription for more.",
            )

    # Create scan record
    from app.models.scan import Scan, ScanStatus

    scan = Scan(
        website_id=website.id,
        status=ScanStatus.PENDING,
    )

    db.add(scan)
    await db.commit()
    await db.refresh(scan)

    # Queue scan job (for now, just return the scan ID)
    # In production, this would send a task to Celery
    # For MVP, we'll run it synchronously in a background task

    return {
        "scan_id": str(scan.id),
        "status": "pending",
        "message": "Scan queued successfully",
    }
