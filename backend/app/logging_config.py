"""Logging configuration for AccessibleAI."""

import logging
import sys
from pathlib import Path
from logging.handlers import RotatingFileHandler, TimedRotatingFileHandler

from app.config import get_settings

settings = get_settings()


def setup_logging() -> logging.Logger:
    """Configure application logging."""

    # Create logger
    logger = logging.getLogger("accessibleai")
    logger.setLevel(logging.DEBUG if settings.debug else logging.INFO)

    # Console handler with colors
    import structlog

    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.DEBUG if settings.debug else logging.INFO)

    # Formatter
    if settings.debug:
        formatter = logging.Formatter(
            '%(asctime)s | %(levelname)-8s | %(name)s:%(lineno)d | %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
    else:
        formatter = logging.Formatter(
            '%(asctime)s | %(levelname)-8s | %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )

    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    # File handler (if log directory exists)
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)

    file_handler = TimedRotatingFileHandler(
        log_dir / "accessibleai.log",
        when="midnight",
        interval=1,
        backupCount=30,
    )
    file_handler.setLevel(logging.INFO)
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    # Error file handler
    error_handler = RotatingFileHandler(
        log_dir / "error.log",
        maxBytes=10_485_760,  # 10MB
        backupCount=5,
    )
    error_handler.setLevel(logging.ERROR)
    error_handler.setFormatter(formatter)
    logger.addHandler(error_handler)

    return logger


# Add logging to Sentry if configured
def setup_sentry():
    """Initialize Sentry error tracking."""
    if settings.sentry_dsn:
        import sentry_sdk

        sentry_sdk.init(
            dsn=settings.sentry_dsn,
            environment="production" if not settings.debug else "development",
            traces_sample_rate=0.1 if settings.debug else 0.05,
            profiles_sample_rate=0.1 if settings.debug else 0.05,
            # Ignore common errors
            ignore_errors=[
                "httpx.TimeoutException",
                "starlette.exceptions.HTTPException",
            ],
            # Integration settings
            integrations=[
                {
                    "id": "fastapi",
                    "auto_enabling_integrations": True,
                    "traces_sample_rate": 0.1,
                },
            ],
        )
        return True
    return False


def get_logger(name: str) -> logging.Logger:
    """Get a logger instance."""
    return logging.getLogger(f"accessibleai.{name}")
