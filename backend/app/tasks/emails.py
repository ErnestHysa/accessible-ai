"""Background tasks for email notifications."""

import asyncio
from datetime import datetime, timedelta
from typing import Optional

from app.worker.celery import celery_app
from app.db.session import async_session_maker
from app.models.scan import Scan
from app.models.website import Website
from app.models.user import User
from app.services.email import EmailService
from sqlalchemy import select


@celery_app.task(bind=True, max_retries=3)
def send_scan_complete_email(self, scan_id: str):
    """
    Send email notification when scan completes.

    Args:
        scan_id: ID of the completed scan
    """
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    try:
        result = loop.run_until_complete(_send_scan_complete_async(scan_id))
        return result
    except Exception as e:
        raise self.retry(exc=e, countdown=60)
    finally:
        loop.close()


async def _send_scan_complete_async(scan_id: str) -> dict:
    """Async implementation of scan completion email."""
    async with async_session_maker() as session:
        # Get scan with related data
        result = await session.execute(
            select(Scan, Website, User)
            .join(Website, Scan.website_id == Website.id)
            .join(User, Website.user_id == User.id)
            .where(Scan.id == scan_id)
        )
        row = result.one_or_none()

        if not row:
            return {"status": "error", "message": "Scan not found"}

        scan, website, user = row

        # Send email
        email_service = EmailService()
        await email_service.send_scan_complete(
            to_email=user.email,
            user_name=user.name,
            website_name=website.name,
            website_url=website.url,
            score=scan.score,
            total_issues=scan.total_issues,
            scan_id=scan_id,
        )

        return {
            "status": "sent",
            "recipient": user.email,
        }


@celery_app.task
def send_weekly_report(user_id: str):
    """
    Send weekly summary report to user.

    Args:
        user_id: ID of the user to send report to
    """
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    try:
        result = loop.run_until_complete(_send_weekly_report_async(user_id))
        return result
    finally:
        loop.close()


async def _send_weekly_report_async(user_id: str) -> dict:
    """Async implementation of weekly report."""
    async with async_session_maker() as session:
        # Get user
        result = await session.execute(select(User).where(User.id == user_id))
        user = result.scalar_one_or_none()

        if not user:
            return {"status": "error", "message": "User not found"}

        # Get scans from the past week
        week_ago = datetime.utcnow() - timedelta(days=7)

        result = await session.execute(
            select(Scan)
            .join(Website, Scan.website_id == Website.id)
            .where(
                Website.user_id == user_id,
                Scan.created_at >= week_ago,
                Scan.status == "completed"
            )
        )
        scans = result.scalars().all()

        if not scans:
            return {"status": "skipped", "message": "No scans this week"}

        # Calculate stats
        total_scans = len(scans)
        avg_score = sum(s.score or 0 for s in scans) / total_scans
        total_issues = sum(s.total_issues or 0 for s in scans)

        # Send email
        email_service = EmailService()
        await email_service.send_weekly_report(
            to_email=user.email,
            user_name=user.name,
            total_scans=total_scans,
            avg_score=int(avg_score),
            total_issues=total_issues,
        )

        return {
            "status": "sent",
            "recipient": user.email,
            "total_scans": total_scans,
        }


@celery_app.task(bind=True, max_retries=3)
def send_welcome_email(self, user_id: str):
    """
    Send welcome email to new users.

    Args:
        user_id: ID of the new user
    """
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    try:
        result = loop.run_until_complete(_send_welcome_async(user_id))
        return result
    except Exception as e:
        raise self.retry(exc=e, countdown=60)
    finally:
        loop.close()


async def _send_welcome_async(user_id: str) -> dict:
    """Async implementation of welcome email."""
    async with async_session_maker() as session:
        result = await session.execute(select(User).where(User.id == user_id))
        user = result.scalar_one_or_none()

        if not user:
            return {"status": "error", "message": "User not found"}

        email_service = EmailService()
        await email_service.send_welcome(
            to_email=user.email,
            user_name=user.name,
        )

        return {"status": "sent", "recipient": user.email}


@celery_app.task
def send_subscription_confirmation(user_id: str, tier: str):
    """
    Send confirmation email for subscription changes.

    Args:
        user_id: ID of the user
        tier: New subscription tier
    """
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    try:
        result = loop.run_until_complete(
            _send_subscription_confirmation_async(user_id, tier)
        )
        return result
    finally:
        loop.close()


async def _send_subscription_confirmation_async(
    user_id: str,
    tier: str
) -> dict:
    """Async implementation of subscription confirmation email."""
    async with async_session_maker() as session:
        result = await session.execute(select(User).where(User.id == user_id))
        user = result.scalar_one_or_none()

        if not user:
            return {"status": "error", "message": "User not found"}

        email_service = EmailService()
        await email_service.send_subscription_confirmation(
            to_email=user.email,
            user_name=user.name,
            tier=tier,
        )

        return {"status": "sent", "recipient": user.email}
