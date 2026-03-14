"""Authentication API tests."""

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async async def test_register_success(client: AsyncClient):
    """Test successful user registration."""
    response = await client.post("/api/v1/auth/register", json={
        "email": "newuser@example.com",
        "password": "SecurePass123!",
        "name": "New User",
    })

    assert response.status_code == 201
    data = response.json()
    assert "access_token" in data
    assert "refresh_token" in data
    assert data["user"]["email"] == "newuser@example.com"
    assert data["user"]["subscription_tier"] == "free"


@pytest.mark.asyncio
async def test_register_duplicate_email(client: AsyncClient):
    """Test registration with duplicate email fails."""
    # First registration
    await client.post("/api/v1/auth/register", json={
        "email": "duplicate@example.com",
        "password": "SecurePass123!",
    })

    # Duplicate registration
    response = await client.post("/api/v1/auth/register", json={
        "email": "duplicate@example.com",
        "password": "SecurePass123!",
    })

    assert response.status_code == 400


@pytest.mark.asyncio
async def test_login_success(client: AsyncClient):
    """Test successful login."""
    # Register first
    await client.post("/api/v1/auth/register", json={
        "email": "login@example.com",
        "password": "SecurePass123!",
    })

    # Login
    response = await client.post("/api/v1/auth/login", json={
        "email": "login@example.com",
        "password": "SecurePass123!",
    })

    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data


@pytest.mark.asyncio
async def test_login_invalid_credentials(client: AsyncClient):
    """Test login with invalid credentials fails."""
    response = await client.post("/api/v1/auth/login", json={
        "email": "nonexistent@example.com",
        "password": "WrongPass123!",
    })

    assert response.status_code == 401


@pytest.mark.asyncio
async def test_get_me_authenticated(client: AsyncClient, auth_headers):
    """Test getting current user info when authenticated."""
    response = await client.get("/api/v1/auth/me", headers=auth_headers)

    assert response.status_code == 200
    data = response.json()
    assert "email" in data


@pytest.mark.asyncio
async def test_get_me_unauthenticated(client: AsyncClient):
    """Test getting current user info fails when not authenticated."""
    response = await client.get("/api/v1/auth/me")

    assert response.status_code == 401


@pytest.fixture
async def client(db_session):
    """Create a test client with database session."""
    from app.main import app

    from fastapi.testclient import TestClient

    # Override the dependency
    from app.core.dependencies import get_db

    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db

    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.clear()
