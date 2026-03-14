"""Main FastAPI application."""

from contextlib import asynccontextmanager
from typing import AsyncIterator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sentry_sdk.integrations.fastapi import FastApiIntegration
from sentry_sdk.integrations.sqlalchemy import SqlalchemyIntegration

from app.config import get_settings
from app.api.v1 import auth, websites, scans, subscriptions

settings = get_settings()

# Initialize Sentry if DSN is provided
if settings.sentry_dsn:
    import sentry_sdk

    sentry_sdk.init(
        dsn=settings.sentry_dsn,
        integrations=[
            FastApiIntegration(),
            SqlalchemyIntegration(),
        ],
        traces_sample_rate=0.1,
        profiles_sample_rate=0.1,
    )


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator:
    """Application lifespan manager."""
    # Startup
    print(f"🚀 {settings.app_name} v{settings.app_version} starting...")
    print(f"📊 Debug mode: {settings.debug}")
    print(f"🔗 API: {settings.base_url}")
    print(f"🎨 Frontend: {settings.frontend_url}")

    yield

    # Shutdown
    print("👋 Shutting down...")


app = FastAPI(
    title=settings.app_name,
    description="AI-powered accessibility compliance for small businesses",
    version=settings.app_version,
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Health check
@app.get("/health")
async def health_check() -> dict:
    """Health check endpoint."""
    return {"status": "healthy", "version": settings.app_version}


# Root endpoint
@app.get("/")
async def root() -> dict:
    """Root endpoint with API information."""
    return {
        "name": settings.app_name,
        "version": settings.app_version,
        "docs": f"{settings.base_url}/docs",
        "health": f"{settings.base_url}/health",
    }


# API routes
app.include_router(auth.router, prefix="/api/v1/auth", tags=["Authentication"])
app.include_router(websites.router, prefix="/api/v1/websites", tags=["Websites"])
app.include_router(scans.router, prefix="/api/v1/scans", tags=["Scans"])
app.include_router(subscriptions.router, prefix="/api/v1", tags=["Subscriptions"])


# Exception handlers
@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """Global exception handler."""
    if settings.debug:
        import traceback

        return JSONResponse(
            status_code=500,
            content={
                "detail": str(exc),
                "traceback": traceback.format_exc(),
            },
        )
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"},
    )
