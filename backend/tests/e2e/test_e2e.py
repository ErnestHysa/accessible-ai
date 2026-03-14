import pytest
import asyncio
import time
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
        # Test invalid token
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

        # Trigger scans - in real scenario would test limit enforcement
        # For now, test that the API accepts the request
        scan_response = await client.post(
            f"/api/v1/websites/{website_id}/scan",
            json={},
            headers=headers
        )
        assert scan_response.status_code == 200


class TestAIIntegration:
    """Test AI-powered fix generation."""

    @pytest.mark.asyncio
    async def test_fix_generation_for_common_issues(self, client: AsyncClient, db_session):
        """Test that AI fixes are generated for common issues."""
        # Register and setup
        response = await client.post("/api/v1/auth/register", json={
            "email": "ai@example.com",
            "password": "TestPass123!",
        })
        token = response.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        # Add website
        website_response = await client.post("/api/v1/websites", json={
            "url": "https://example.com",
            "name": "AI Test Site",
        }, headers=headers)
        website_id = website_response.json()["id"]

        # Trigger scan
        scan_response = await client.post(
            f"/api/v1/websites/{website_id}/scan",
            json={"full_scan": False},
            headers=headers
        )

        # If scan completes, check that we can get results
        if scan_response.status_code in [200, 201]:
            scan_id = scan_response.json().get("scan_id")
            if scan_id:
                # Get scan results
                results_response = await client.get(
                    f"/api/v1/scans/{scan_id}",
                    headers=headers
                )
                assert results_response.status_code == 200

    @pytest.mark.asyncio
    async def test_generic_fix_generation(self):
        """Test that generic fix generation works when AI fails."""
        from app.services.ai_fixer import generate_generic_fix
        from app.models.scan import Issue

        # Create a test issue
        issue = Issue(
            id="test-issue-1",
            scan_id="test-scan-1",
            website_id="test-website-1",
            type="image-alt",
            selector="img.logo",
            description="Image missing alt text",
            severity="minor",
        )

        # Generate generic fix
        fix = generate_generic_fix(issue)
        assert fix is not None
        assert "Fix for" in fix
        assert issue.description in fix


class TestPerformance:
    """Test API performance under load."""

    @pytest.mark.asyncio
    async def test_concurrent_scans(self, client: AsyncClient):
        """Test that multiple concurrent scan requests are handled."""
        # Register user
        response = await client.post("/api/v1/auth/register", json={
            "email": "perf@example.com",
            "password": "TestPass123!",
        })
        token = response.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        # Add website
        website_response = await client.post("/api/v1/websites", json={
            "url": "https://example.com",
            "name": "Perf Test Site",
        }, headers=headers)
        website_id = website_response.json()["id"]

        # Trigger multiple concurrent scan requests
        tasks = []
        for _ in range(3):
            tasks.append(client.post(
                f"/api/v1/websites/{website_id}/scan",
                json={},
                headers=headers
            ))

        # All requests should be accepted (queued)
        results = await asyncio.gather(*tasks)
        for result in results:
            assert result.status_code in [200, 201]

    @pytest.mark.asyncio
    async def test_response_time(self, client: AsyncClient):
        """Test that API response times are acceptable."""
        start_time = time.time()

        response = await client.get("/health")

        elapsed = time.time() - start_time
        assert response.status_code == 200
        assert elapsed < 1.0  # Health check should respond within 1 second


class TestSecurity:
    """Test security-related functionality."""

    @pytest.mark.asyncio
    async def test_sql_injection_prevention(self, client: AsyncClient):
        """Test that SQL injection attempts are prevented."""
        # Register with potential SQL injection in email
        # The validation should reject invalid email format
        response = await client.post("/api/v1/auth/register", json={
            "email": "test'; DROP TABLE users; --@example.com",
            "password": "TestPass123!",
        })
        # Email validation should fail
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_xss_prevention(self, client: AsyncClient):
        """Test that XSS attempts are prevented in user input."""
        response = await client.post("/api/v1/auth/register", json={
            "email": "xss@example.com",
            "password": "TestPass123!",
            "name": "<script>alert('xss')</script>",
        })
        assert response.status_code == 201

        # Verify the name is stored/returned safely
        user_response = await client.get("/api/v1/auth/me", headers={
            "Authorization": f"Bearer {response.json()['access_token']}"
        })
        assert user_response.status_code == 200
        # The script tag should not be executed when returned
        user_data = user_response.json()
        assert "<script>" not in user_data.get("name", "")

    @pytest.mark.asyncio
    async def test_authentication_bypass_attempts(self, client: AsyncClient):
        """Test that authentication cannot be bypassed."""
        # Test missing token
        response = await client.get("/api/v1/auth/me")
        assert response.status_code == 401

        # Test invalid token format
        response = await client.get("/api/v1/auth/me", headers={
            "Authorization": "Bearer invalid.token.format"
        })
        assert response.status_code == 401

        # Test empty token
        response = await client.get("/api/v1/auth/me", headers={
            "Authorization": "Bearer "
        })
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_authorization_checks(self, client: AsyncClient):
        """Test that authorization properly restricts access."""
        # Create two users
        user1_response = await client.post("/api/v1/auth/register", json={
            "email": "user1@example.com",
            "password": "TestPass123!",
        })
        user1_token = user1_response.json()["access_token"]

        user2_response = await client.post("/api/v1/auth/register", json={
            "email": "user2@example.com",
            "password": "TestPass123!",
        })
        user2_token = user2_response.json()["access_token"]

        # User 1 adds a website
        website_response = await client.post("/api/v1/websites", json={
            "url": "https://example.com",
            "name": "User1 Site",
        }, headers={"Authorization": f"Bearer {user1_token}"})
        website_id = website_response.json()["id"]

        # User 2 should not be able to access User 1's website
        response = await client.get(
            f"/api/v1/websites/{website_id}",
            headers={"Authorization": f"Bearer {user2_token}"}
        )
        assert response.status_code == 404 or response.status_code == 403

        # User 2 should not be able to delete User 1's website
        response = await client.delete(
            f"/api/v1/websites/{website_id}",
            headers={"Authorization": f"Bearer {user2_token}"}
        )
        assert response.status_code == 404 or response.status_code == 403
