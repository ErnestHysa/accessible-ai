"""Celery worker configuration for background tasks."""

from celery import Celery
from app.config import get_settings

settings = get_settings()

# Create Celery app
celery_app = Celery(
    "accessibleai",
    broker=settings.redis_url,
    backend=settings.redis_url,
    include=[
        "app.tasks.scans",
        "app.tasks.emails",
        "app.tasks.reports",
    ],
)

# Celery configuration
celery_app.conf.update(
    # Task settings
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    # Task routing
    task_routes={
        "app.tasks.scans.*": {"queue": "scans"},
        "app.tasks.emails.*": {"queue": "emails"},
        "app.tasks.reports.*": {"queue": "reports"},
    },
    # Task result settings
    result_expires=3600,
    task_track_started=True,
    task_time_limit=3600,  # 1 hour max per task
    task_soft_time_limit=3000,  # 50 minutes soft limit
    # Worker settings
    worker_prefetch_multiplier=4,
    worker_max_tasks_per_child=1000,
    # Rate limiting
    task_annotations={
        "app.tasks.scans.run_accessibility_scan": {"rate_limit": "10/m"},
    },
    # Retry settings
    task_acks_late=True,
    task_reject_on_worker_lost=True,
)

# Optional: Configure Celery Beat schedule
celery_app.conf.beat_schedule = {
    # Daily cleanup of old scan results
    "cleanup-old-scans": {
        "task": "app.tasks.scans.cleanup_old_scans",
        "schedule": 86400.0,  # Daily
    },
    # Daily usage report generation
    "generate-daily-reports": {
        "task": "app.tasks.reports.generate_daily_usage",
        "schedule": 86400.0,  # Daily at midnight
    },
}


@celery_app.task(bind=True, max_retries=3)
def debug_task(self):
    """Test task for verifying Celery worker is functioning."""
    print(f"Request: {self.request!r}")
    return f"Celery worker is running! Task ID: {self.request.id}"


# Health check for monitoring
@celery_app.task
def health_check():
    """Health check task that verifies Celery is working."""
    return {"status": "healthy", "message": "Celery worker is operational"}
