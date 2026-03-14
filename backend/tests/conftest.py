"""Test configuration for pytest."""

import asyncio
import pytest
from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.pool import NullPool

from app.models.base import Base
from app.config import get_settings

TEST_DATABASE_URL = "postgresql+asyncpg://test:test@localhost:5432/test_accessible_ai"


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="function")
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    """Create a fresh database session for each test."""
    engine = create_async_engine(
        TEST_DATABASE_URL,
        poolclass=NullPool,
    )

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async_session_maker = async_sessionmaker(
        engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )

    async with async_session_maker() as session:
        yield session

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest.fixture
def test_user_data():
    """Sample user data for testing."""
    return {
        "email": "test@example.com",
        "password": "TestPassword123!",
        "name": "Test User",
    }


@pytest.fixture
def test_website_data():
    """Sample website data for testing."""
    return {
        "url": "https://example.com",
        "name": "Example Site",
        "platform": "generic",
    }


@pytest.fixture
def auth_headers(client):
    """Get authentication headers for API requests."""
    # Register and login to get token
    response = client.post("/api/v1/auth/register", json={
        "email": "test@example.com",
        "password": "TestPassword123!",
        "name": "Test User",
    })
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}
