"""Background tasks for accessibility scanning."""

import asyncio
from datetime import datetime, timedelta
from typing import Optional
from celery import current_task
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.worker.celery import celery_app
from app.db.session import async_session_maker
from app.models.scan import Scan, ScanStatus
from app.models.website import Website
from app.models.usage import UsageRecord, UsageType
from app.services.scanner import AccessibilityScanner
from app.services.ai_fixer import AIFixerService


@celery_app.task(bind=True, max_retries=3)
def run_accessibility_scan(self, scan_id: str, website_id: str, user_id: str):
    """
    Run accessibility scan in the background.

    Args:
        scan_id: ID of the scan record
        website_id: ID of the website to scan
        user_id: ID of the user who requested the scan
    """
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    try:
        result = loop.run_until_complete(
            _run_scan_async(scan_id, website_id, user_id)
        )
        return result
    except Exception as e:
        # Update scan status to failed
        loop.run_until_complete(
            _update_scan_status(scan_id, ScanStatus.FAILED, str(e))
        )
        raise self.retry(exc=e, countdown=60)
    finally:
        loop.close()


async def _run_scan_async(scan_id: str, website_id: str, user_id: str) -> dict:
    """Async implementation of scan execution."""
    async with async_session_maker() as session:
        # Get website
        result = await session.execute(select(Website).where(Website.id == website_id))
        website = result.scalar_one_or_none()

        if not website:
            raise ValueError(f"Website {website_id} not found")

        # Get scan
        result = await session.execute(select(Scan).where(Scan.id == scan_id))
        scan = result.scalar_one_or_none()

        if not scan:
            raise ValueError(f"Scan {scan_id} not found")

        # Update status to running
        scan.status = ScanStatus.RUNNING
        await session.commit()

        # Run scanner
        scanner = AccessibilityScanner()
        scan_result = await scanner.scan_website(website.url)

        # Process results with AI fixer
        fixer = AIFixerService()
        issues_with_fixes = []
        for issue in scan_result.get("issues", []):
            fix = await fixer.generate_fix(issue)
            issues_with_fixes.append({**issue, "ai_fix": fix})

        # Update scan with results
        scan.status = ScanStatus.COMPLETED
        scan.score = scan_result.get("score", 0)
        scan.total_issues = scan_result.get("total_issues", 0)
        scan.critical_issues = scan_result.get("critical_issues", 0)
        scan.serious_issues = scan_result.get("serious_issues", 0)
        scan.moderate_issues = scan_result.get("moderate_issues", 0)
        scan.minor_issues = scan_result.get("minor_issues", 0)
        scan.completed_at = datetime.utcnow()
        await session.commit()

        # Record usage
        usage_record = UsageRecord(
            user_id=user_id,
            website_id=website_id,
            scan_id=scan_id,
            usage_type=UsageType.SCAN,
            quantity=1,
        )
        session.add(usage_record)
        await session.commit()

        return {
            "scan_id": scan_id,
            "score": scan.score,
            "total_issues": scan.total_issues,
            "status": "completed",
        }


async def _update_scan_status(
    scan_id: str,
    status: ScanStatus,
    error_message: Optional[str] = None
):
    """Update scan status after failure."""
    async with async_session_maker() as session:
        result = await session.execute(select(Scan).where(Scan.id == scan_id))
        scan = result.scalar_one_or_none()
        if scan:
            scan.status = status
            if error_message:
                scan.error_message = error_message
            await session.commit()


@celery_app.task
def cleanup_old_scans():
    """
    Clean up old scan records to manage database size.

    Removes scans older than 90 days for free tier,
    1 year for paid tiers.
    """
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    try:
        loop.run_until_complete(_cleanup_scans_async())
        return {"status": "completed", "message": "Old scans cleaned up"}
    finally:
        loop.close()


async def _cleanup_scans_async():
    """Async implementation of scan cleanup."""
    async with async_session_maker() as session:
        # Delete scans older than 90 days that are completed
        cutoff_date = datetime.utcnow() - timedelta(days=90)

        # In production, you might want to archive instead of delete
        # This is a simplified version
        await session.execute(
            f"DELETE FROM scans WHERE status = 'completed' AND completed_at < '{cutoff_date}'"
        )
        await session.commit()


@celery_app.task
def queue_scan(website_id: str, user_id: str, full_scan: bool = False) -> dict:
    """
    Queue a new accessibility scan.

    Args:
        website_id: ID of the website to scan
        user_id: ID of the user requesting the scan
        full_scan: Whether to run a full scan (vs incremental)

    Returns:
        Dict with scan_id and status
    """
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    try:
        result = loop.run_until_complete(
            _queue_scan_async(website_id, user_id, full_scan)
        )
        return result
    finally:
        loop.close()


async def _queue_scan_async(
    website_id: str,
    user_id: str,
    full_scan: bool
) -> dict:
    """Async implementation of scan queuing."""
    async with async_session_maker() as session:
        # Verify website exists and belongs to user
        result = await session.execute(
            select(Website).where(
                Website.id == website_id,
                Website.user_id == user_id
            )
        )
        website = result.scalar_one_or_none()

        if not website:
            raise ValueError("Website not found or access denied")

        # Create scan record
        scan = Scan(
            website_id=website_id,
            user_id=user_id,
            status=ScanStatus.PENDING,
            full_scan=full_scan,
        )
        session.add(scan)
        await session.commit()
        await session.refresh(scan)

        # Trigger the actual scan task
        run_accessibility_scan.delay(scan.id, website_id, user_id)

        return {
            "scan_id": scan.id,
            "status": "pending",
            "message": "Scan queued successfully",
        }
