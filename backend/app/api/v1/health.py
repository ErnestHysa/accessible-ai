"""Health check endpoints for monitoring."""

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from redis.asyncio import Redis
import time

from app.core.dependencies import get_db
from app.config import get_settings

router = APIRouter(tags=["Health"])
settings = get_settings()


@router.get("/health")
async def health_check():
    """Basic health check endpoint."""
    return {
        "status": "healthy",
        "timestamp": time.time(),
        "version": settings.app_version,
    }


@router.get("/health/db")
async def database_health(db: AsyncSession = Depends(get_db)):
    """Check database connectivity."""
    start_time = time.time()
    try:
        # Simple query to test connection
        await db.execute("SELECT 1")
        response_time = (time.time() - start_time) * 1000
        return {
            "status": "healthy",
            "response_time_ms": round(response_time, 2),
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e),
        }


@router.get("/health/redis")
async def redis_health():
    """Check Redis connectivity."""
    start_time = time.time()
    try:
        redis = Redis.from_url(settings.redis_url)
        await redis.ping()
        await redis.close()
        response_time = (time.time() - start_time) * 1000
        return {
            "status": "healthy",
            "response_time_ms": round(response_time, 2),
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e),
        }


@router.get("/health/celery")
async def celery_health():
    """Check Celery worker status."""
    try:
        from app.worker.celery import app as celery_app

        # Check if workers are available
        inspect = celery_app.control.inspect()
        active_workers = inspect.active()
        if active_workers:
            return {
                "status": "healthy",
                "workers": list(active_workers.keys()),
                "worker_count": len(active_workers),
            }
        else:
            return {
                "status": "unhealthy",
                "error": "No active workers found",
            }
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e),
        }


@router.get("/health/detailed")
async def detailed_health_check(db: AsyncSession = Depends(get_db)):
    """Comprehensive health check for all services."""
    health_status = {
        "status": "healthy",
        "timestamp": time.time(),
        "version": settings.app_version,
        "services": {},
    }

    # Check database
    start_time = time.time()
    try:
        await db.execute("SELECT 1")
        health_status["services"]["database"] = {
            "status": "healthy",
            "response_time_ms": round((time.time() - start_time) * 1000, 2),
        }
    except Exception as e:
        health_status["services"]["database"] = {
            "status": "unhealthy",
            "error": str(e),
        }
        health_status["status"] = "degraded"

    # Check Redis
    start_time = time.time()
    try:
        redis = Redis.from_url(settings.redis_url)
        await redis.ping()
        await redis.close()
        health_status["services"]["redis"] = {
            "status": "healthy",
            "response_time_ms": round((time.time() - start_time) * 1000, 2),
        }
    except Exception as e:
        health_status["services"]["redis"] = {
            "status": "unhealthy",
            "error": str(e),
        }
        health_status["status"] = "degraded"

    # Check Celery
    try:
        from app.worker.celery import app as celery_app
        inspect = celery_app.control.inspect()
        active_workers = inspect.active()
        if active_workers:
            health_status["services"]["celery"] = {
                "status": "healthy",
                "worker_count": len(active_workers),
            }
        else:
            health_status["services"]["celery"] = {
                "status": "unhealthy",
                "error": "No active workers",
            }
            health_status["status"] = "degraded"
    except Exception as e:
        health_status["services"]["celery"] = {
            "status": "unhealthy",
            "error": str(e),
        }
        health_status["status"] = "degraded"

    return health_status
