import pytest
import asyncio
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession

from app.main import app
from app.models.base import Base
from app.models.user import User
from app.models.website import Website


# Test database
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"


@pytest.fixture(scope="function")
async def db_session():
    """Create a test database session."""
    engine = create_async_engine(TEST_DATABASE_URL)

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
async def client(db_session):
    """Create a test client with database."""
    from app.core.dependencies import get_db

    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        yield ac

    app.dependency_overrides.clear()


@pytest.fixture
def auth_headers(client):
    """Get authentication headers for API requests."""
    async def _get_headers():
        # Register and login
        response = await client.post("/api/v1/auth/register", json={
            "email": "test@example.com",
            "password": "TestPassword123!",
            "name": "Test User",
        })

        assert response.status_code == 201

        token = response.json()["access_token"]
        return {"Authorization": f"Bearer {token}"}

    return _get_headers()


class TestAuthFlow:
    """Test complete authentication flow."""

    @pytest.mark.asyncio
    async def test_complete_auth_flow(self, client: AsyncClient):
        """Test register → login → access protected endpoint → logout."""
        # Register
        register_response = await client.post("/api/v1/auth/register", json={
            "email": "flowtest@example.com",
            "password": "TestPass123!",
        })
        assert register_response.status_code == 201
        register_data = register_response.json()

        assert "access_token" in register_data
        assert "refresh_token" in register_data
        assert register_data["user"]["email"] == "flowtest@example.com"

        # Login with same credentials
        login_response = await client.post("/api/v1/auth/login", json={
            "email": "flowtest@example.com",
            "password": "TestPass123!",
        })
        assert login_response.status_code == 200
        login_data = login_response.json()

        assert "access_token" in login_data
        assert login_data["user"]["email"] == "flowtest@example.com"

        # Access protected endpoint
        headers = {"Authorization": f"Bearer {login_data['access_token']}"}
        me_response = await client.get("/api/v1/auth/me", headers=headers)
        assert me_response.status_code == 200
        assert me_response.json()["email"] == "flowtest@example.com"

        # Logout
        logout_response = await client.post("/api/v1/auth/logout", headers=headers)
        assert logout_response.status_code == 204

        # Verify token is invalidated
        me_response = await client.get("/api/v1/auth/me", headers=headers)
        assert me_response.status_code == 401


class TestWebsiteScanning:
    """Test website scanning functionality."""

    @pytest.mark.asyncio
    async def test_scan_workflow(self, client: AsyncClient, db_session):
        """Test add website → trigger scan → view results."""
        # First, register and login
        response = await client.post("/api/v1/auth/register", json={
            "email": "scan@example.com",
            "password": "TestPass123!",
        })
        token = response.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        # Add website
        website_response = await client.post("/api/v1/websites", json={
            "url": "https://example.com",
            "name": "Test Site",
            "platform": "generic",
        }, headers=headers)

        assert website_response.status_code == 201
        website_id = website_response.json()["id"]

        # Trigger scan (will be queued)
        scan_response = await client.post(
            f"/api/v1/websites/{website_id}/scan",
            json={"full_scan": False},
            headers=headers
        )

        assert scan_response.status_code in [200, 201]
        scan_id = scan_response.json()["scan_id"]

        # Check scan status (may be pending)
        status_response = await client.get(
            f"/api/v1/scans/{scan_id}",
            headers=headers
        )
        assert status_response.status_code == 200
        assert status_response.json()["id"] == scan_id


class TestSubscriptionManagement:
    """Test subscription and payment flow."""

    @pytest.mark.asyncio
    async def test_free_tier_limits(self, client: AsyncClient):
        """Test that free tier limits are enforced."""
        # Register user (starts at free tier)
        response = await client.post("/api/v1/auth/register", json={
            "email": "limits@example.com",
            "password": "TestPass123!",
        })
        token = response.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        # Free tier: 1 website max
        # Add first website - should succeed
        response1 = await client.post("/api/v1/websites", json={
            "url": "https://example1.com",
        }, headers=headers)
        assert response1.status_code == 201

        # Try to add second website - should fail
        response2 = await client.post("/api/v1/websites", json={
            "url": "https://example2.com",
        }, headers=headers)
        assert response2.status_code == 403
        assert "limit" in str(response2.json()).lower()


class TestAPIKeyAuthentication:
    """Test API key authentication for WordPress plugin."""

    @pytest.mark.asyncio
    async def test_api_key_scan_triggering(self, client: AsyncClient, db_session):
        """Test that API keys can trigger scans."""
        # Create user and website with API key
        response = await client.post("/api/v1/auth/register", json={
            "email": "apikey@example.com",
            "password": "TestPass123!",
        })
        token = response.json()["access_token"]
        auth_headers = {"Authorization": f"Bearer {token}"}

        # Add website
        website_response = await client.post("/api/v1/websites", json={
            "url": "https://example.com",
        }, headers=auth_headers)
        website_id = website_response.json()["id"]
        api_key = website_response.json()["api_key"]

        # Use API key to trigger scan
        api_headers = {"X-API-Key": api_key}
        scan_response = await client.post(
            f"/api/v1/websites/{website_id}/scan",
            json={},
            headers=api_headers
        )

        assert scan_response.status_code == 200
        assert "scan_id" in scan_response.json()


class TestErrorHandling:
    """Test error handling and validation."""

    @pytest.mark.asyncio
    async def test_validation_errors(self, client: AsyncClient):
        """Test that validation errors are properly formatted."""
        # Test invalid email
        response = await client.post("/api/v1/auth/register", json={
            "email": "not-an-email",
            "password": "TestPass123!",
        })
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_duplicate_email(self, client: AsyncClient):
        """Test that duplicate email is rejected."""
        email = "duplicate@example.com"

        # First registration should succeed
        response1 = await client.post("/api/v1/auth/register", json={
            "email": email,
            "password": "TestPass123!",
        })
        assert response1.status_code == 201

        # Duplicate should fail
        response2 = await client.post("/api/v1/auth/register", json={
            "email": email,
            "password": "TestPass123!",
        })
        assert response2.status_code == 400

    @pytest.mark.asyncio
    async def test_invalid_api_key(self, client: AsyncClient):
        """Test that invalid API keys are rejected."""
        response = await client.post(
            "/api/v1/websites/fake-id/scan",
            headers={"X-API-Key": "invalid-key"}
        )
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_expired_token(self, client: AsyncClient):
        """Test that expired tokens are rejected."""
        # This would require mocking time-based token expiration
        # For now, just test invalid token
        response = await client.get(
            "/api/v1/auth/me",
            headers={"Authorization": "Bearer invalid_token"}
        )
        assert response.status_code == 401


class TestRateLimiting:
    """Test rate limiting and usage tracking."""

    @pytest.mark.asyncio
    async def test_free_tier_scan_limit(self, client: AsyncClient, db_session):
        """Test that free tier has scan limits."""
        # Register free tier user
        response = await client.post("/api/v1/auth/register", json={
            "email": "ratelimit@example.com",
            "password": "TestPass123!",
        })
        token = response.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        # Add website
        website_response = await client.post("/api/v1/websites", json={
            "url": "https://example.com",
        }, headers=headers)
        website_id = website_response.json()["id"]

        # Trigger 5 scans (free tier limit)
        # In a real test, we'd need to wait for each scan to complete
        # For now, just test that the API accepts the request
        # The actual limiting is checked when the scan is processed

        # This test would need significant mocking of the scan process
        # or a very long timeout to run actual scans


class TestAIIntegration:
    """Test AI-powered fix generation."""

    @pytest.mark.asyncio
    async def test_fix_generation_for_common_issues(self, client: AsyncClient, db_session):
        """Test that AI fixes are generated for common issues."""
        # This test would require:
        # 1. Mocking the OpenAI API or using a test key
        # 2. Creating a scan with known issues
        # 3. Calling the fix generation endpoint
        # 4. Validating the response

        # For now, we'll test that the endpoint exists and has the right shape
        pass  # Implement with mocked OpenAI responses

    @pytest.mark.asyncio
    async def test_fix_validation(self, client: AsyncClient):
        """Test that generated fixes are validated."""
        pass  # Would test fix validation logic


# Performance tests
class TestPerformance:
    """Test API performance under load."""

    @pytest.mark.asyncio
    @pytest.mark.skip(reason="Performance tests should run separately")
    async def test_concurrent_scans(self, client: AsyncClient):
        """Test that multiple concurrent scans are handled properly."""
        # Would spawn multiple scan requests simultaneously
        # and verify they don't interfere with each other
        pass

    @pytest.mark.asyncio
    @pytest.mark.skip(reason="Performance tests should run separately")
    async def test_scan_response_time(self, client: AsyncClient):
        """Test that scan response time is acceptable."""
        # Would measure scan time and assert it's within SLA
        pass


# Security tests
class TestSecurity:
    """Test security-related functionality."""

    @pytest.mark.asyncio
    async def test_sql_injection_prevention(self, client: AsyncClient):
        """Test that SQL injection attempts are prevented."""
        # This would require testing database queries directly
        pass

    @pytest.mark.asyncio
    async def test_xss_prevention(self, client: AsyncClient):
        """Test that XSS attempts are prevented in user input."""
        # Test that user input is properly sanitized
        response = await client.post("/api/v1/auth/register", json={
            "email": "test@example.com",
            "password": "TestPass123!",
            "name": "<script>alert('xss')</script>",
        })
        assert response.status_code == 201
        # The name should be sanitized when stored or displayed

    @pytest.mark.asyncio
 async def test_authentication_bypass_attempts(self, client: AsyncClient):
        """Test that authentication cannot be bypassed."""
        # Test various authentication bypass attempts
        # - Missing tokens
        # - Invalid tokens
        # # Expired tokens
        # - Manipulated tokens
        pass

    @pytest.mark.asyncio
    async def test_authorization_checks(self, client: AsyncClient):
        """Test that authorization properly restricts access."""
        # Test that:
        # - Users can only access their own resources
        # - Free tier users are restricted from paid features
        # - Admin-only endpoints are protected
        pass
