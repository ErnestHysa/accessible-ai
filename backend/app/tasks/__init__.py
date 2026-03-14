"""Background tasks for AccessibleAI."""

from app.tasks.scans import (
    run_accessibility_scan,
    cleanup_old_scans,
    queue_scan,
)
from app.tasks.emails import (
    send_scan_complete_email,
    send_weekly_report,
)
from app.tasks.reports import (
    generate_daily_usage,
    generate_user_report,
)

__all__ = [
    "run_accessibility_scan",
    "cleanup_old_scans",
    "queue_scan",
    "send_scan_complete_email",
    "send_weekly_report",
    "generate_daily_usage",
    "generate_user_report",
]
