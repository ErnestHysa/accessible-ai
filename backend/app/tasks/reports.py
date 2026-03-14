"""Background tasks for report generation."""

import asyncio
from datetime import datetime, timedelta
from typing import Optional

from app.worker.celery import celery_app
from app.db.session import async_session_maker
from app.models.usage import UsageRecord, UsageType
from app.models.user import User
from app.models.website import Website
from app.models.scan import Scan
from sqlalchemy import select, func


@celery_app.task
def generate_daily_usage():
    """
    Generate daily usage statistics for monitoring and billing.

    This task runs daily to calculate aggregate usage metrics.
    """
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    try:
        result = loop.run_until_complete(_generate_daily_usage_async())
        return result
    finally:
        loop.close()


async def _generate_daily_usage_async() -> dict:
    """Async implementation of daily usage generation."""
    async with async_session_maker() as session:
        yesterday = datetime.utcnow() - timedelta(days=1)
        start_of_day = yesterday.replace(hour=0, minute=0, second=0, microsecond=0)
        end_of_day = yesterday.replace(hour=23, minute=59, second=59, microsecond=999999)

        # Get usage stats
        result = await session.execute(
            select(
                func.count(UsageRecord.id).label("total_scans"),
                func.count(func.distinct(UsageRecord.user_id)).label("active_users"),
                func.count(func.distinct(UsageRecord.website_id)).label("websites_scanned"),
            ).where(
                UsageRecord.created_at >= start_of_day,
                UsageRecord.created_at <= end_of_day,
            )
        )
        stats = result.one()

        return {
            "date": yesterday.date().isoformat(),
            "total_scans": stats.total_scans or 0,
            "active_users": stats.active_users or 0,
            "websites_scanned": stats.websites_scanned or 0,
        }


@celery_app.task
def generate_user_report(user_id: str, days: int = 30):
    """
    Generate usage report for a specific user.

    Args:
        user_id: ID of the user
        days: Number of days to include in report (default 30)
    """
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    try:
        result = loop.run_until_complete(
            _generate_user_report_async(user_id, days)
        )
        return result
    finally:
        loop.close()


async def _generate_user_report_async(user_id: str, days: int) -> dict:
    """Async implementation of user report generation."""
    async with async_session_maker() as session:
        cutoff_date = datetime.utcnow() - timedelta(days=days)

        # Get user's websites
        websites_result = await session.execute(
            select(Website).where(Website.user_id == user_id)
        )
        websites = websites_result.scalars().all()

        if not websites:
            return {"status": "error", "message": "No websites found for user"}

        website_ids = [w.id for w in websites]

        # Get scan stats
        scans_result = await session.execute(
            select(
                func.count(Scan.id).label("total_scans"),
                func.avg(Scan.score).label("avg_score"),
                func.sum(Scan.total_issues).label("total_issues"),
            ).where(
                Scan.website_id.in_(website_ids),
                Scan.created_at >= cutoff_date,
                Scan.status == "completed"
            )
        )
        scan_stats = scans_result.one()

        # Get usage records
        usage_result = await session.execute(
            select(
                func.count(UsageRecord.id).label("total_usage"),
                func.sum(UsageRecord.quantity).label("total_quantity"),
            ).where(
                UsageRecord.user_id == user_id,
                UsageRecord.created_at >= cutoff_date,
            )
        )
        usage_stats = usage_result.one()

        # Get recent scans
        recent_scans_result = await session.execute(
            select(Scan)
            .where(
                Scan.website_id.in_(website_ids),
                Scan.status == "completed"
            )
            .order_by(Scan.created_at.desc())
            .limit(10)
        )
        recent_scans = recent_scans_result.scalars().all()

        return {
            "user_id": user_id,
            "period_days": days,
            "websites_count": len(websites),
            "total_scans": scan_stats.total_scans or 0,
            "average_score": float(scan_stats.avg_score or 0),
            "total_issues_found": scan_stats.total_issues or 0,
            "total_usage_records": usage_stats.total_usage or 0,
            "recent_scans": [
                {
                    "id": s.id,
                    "website_id": s.website_id,
                    "score": s.score,
                    "total_issues": s.total_issues,
                    "created_at": s.created_at.isoformat(),
                }
                for s in recent_scans
            ],
        }


@celery_app.task
def generate_health_report():
    """
    Generate system health report for monitoring.

    Returns various metrics about system health.
    """
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    try:
        result = loop.run_until_complete(_generate_health_report_async())
        return result
    finally:
        loop.close()


async def _generate_health_report_async() -> dict:
    """Async implementation of health report generation."""
    async with async_session_maker() as session:
        # Get user count
        users_result = await session.execute(
            select(func.count(User.id))
        )
        total_users = users_result.scalar() or 0

        # Get website count
        websites_result = await session.execute(
            select(func.count(Website.id))
        )
        total_websites = websites_result.scalar() or 0

        # Get scan stats
        scans_result = await session.execute(
            select(
                func.count(Scan.id).label("total"),
                func.sum(
                    func.case(
                        (Scan.status == "completed", 1),
                        else_=0
                    )
                ).label("completed"),
                func.sum(
                    func.case(
                        (Scan.status == "pending", 1),
                        else_=0
                    )
                ).label("pending"),
                func.sum(
                    func.case(
                        (Scan.status == "running", 1),
                        else_=0
                    )
                ).label("running"),
                func.sum(
                    func.case(
                        (Scan.status == "failed", 1),
                        else_=0
                    )
                ).label("failed"),
            )
        )
        scan_stats = scans_result.one()

        # Get recent activity (last 24 hours)
        yesterday = datetime.utcnow() - timedelta(days=1)
        recent_result = await session.execute(
            select(func.count(Scan.id)).where(
                Scan.created_at >= yesterday
            )
        )
        recent_scans = recent_result.scalar() or 0

        return {
            "timestamp": datetime.utcnow().isoformat(),
            "users": {
                "total": total_users,
            },
            "websites": {
                "total": total_websites,
            },
            "scans": {
                "total": scan_stats.total or 0,
                "completed": scan_stats.completed or 0,
                "pending": scan_stats.pending or 0,
                "running": scan_stats.running or 0,
                "failed": scan_stats.failed or 0,
                "last_24_hours": recent_scans,
            },
        }
