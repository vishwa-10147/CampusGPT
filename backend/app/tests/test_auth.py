# ==============================================================================
# CampusGPT Backend — Auth Tests
# ==============================================================================
import pytest
from httpx import AsyncClient


class TestAuth:
    """Authentication endpoint tests."""

    @pytest.mark.asyncio
    async def test_register_success(self, client: AsyncClient, sample_user_data):
        """Test successful user registration."""
        response = await client.post("/api/v1/auth/register", json=sample_user_data)
        assert response.status_code == 201
        data = response.json()
        assert data["email"] == sample_user_data["email"]
        assert data["full_name"] == sample_user_data["full_name"]
        assert "id" in data
        assert "created_at" in data

    @pytest.mark.asyncio
    async def test_register_duplicate_email(self, client: AsyncClient, sample_user_data):
        """Test registration with duplicate email fails."""
        # First registration
        await client.post("/api/v1/auth/register", json=sample_user_data)

        # Second registration with same email
        response = await client.post("/api/v1/auth/register", json=sample_user_data)
        assert response.status_code == 400
        assert "already registered" in response.json()["detail"].lower()

    @pytest.mark.asyncio
    async def test_register_password_mismatch(self, client: AsyncClient):
        """Test registration with password mismatch fails."""
        data = {
            "email": "test2@college.edu",
            "password": "password123",
            "password_confirm": "differentpassword",
            "full_name": "Test User",
        }
        response = await client.post("/api/v1/auth/register", json=data)
        assert response.status_code == 400
        assert "passwords do not match" in response.json()["detail"].lower()

    @pytest.mark.asyncio
    async def test_register_invalid_email(self, client: AsyncClient):
        """Test registration with invalid email fails."""
        data = {
            "email": "invalid-email",
            "password": "password123",
            "password_confirm": "password123",
            "full_name": "Test User",
        }
        response = await client.post("/api/v1/auth/register", json=data)
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_register_short_password(self, client: AsyncClient):
        """Test registration with short password fails."""
        data = {
            "email": "test3@college.edu",
            "password": "short",
            "password_confirm": "short",
            "full_name": "Test User",
        }
        response = await client.post("/api/v1/auth/register", json=data)
        assert response.status_code == 422
        detail = response.json()["detail"]
        if isinstance(detail, list):
            detail = str(detail)
        assert "at least 8 characters" in detail.lower()

    @pytest.mark.asyncio
    async def test_login_success(self, client: AsyncClient, sample_user_data):
        """Test successful login."""
        # Register first
        await client.post("/api/v1/auth/register", json=sample_user_data)

        # Login
        response = await client.post("/api/v1/auth/login", json={
            "email": sample_user_data["email"],
            "password": sample_user_data["password"],
        })
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"
        assert "expires_in" in data

        # Check cookies are set
        assert "access_token" in response.cookies
        assert "refresh_token" in response.cookies

    @pytest.mark.asyncio
    async def test_login_wrong_password(self, client: AsyncClient, sample_user_data):
        """Test login with wrong password fails."""
        await client.post("/api/v1/auth/register", json=sample_user_data)

        response = await client.post("/api/v1/auth/login", json={
            "email": sample_user_data["email"],
            "password": "wrongpassword",
        })
        assert response.status_code == 401
        assert "invalid credentials" in response.json()["detail"].lower()

    @pytest.mark.asyncio
    async def test_login_nonexistent_user(self, client: AsyncClient):
        """Test login with nonexistent user fails."""
        response = await client.post("/api/v1/auth/login", json={
            "email": "nonexistent@college.edu",
            "password": "password123",
        })
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_me_unauthenticated(self, client: AsyncClient):
        """Test /me endpoint without authentication fails."""
        response = await client.get("/api/v1/auth/me")
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_me_authenticated(self, client: AsyncClient, sample_user_data):
        """Test /me endpoint with authentication succeeds."""
        await client.post("/api/v1/auth/register", json=sample_user_data)
        await client.post("/api/v1/auth/login", json={
            "email": sample_user_data["email"],
            "password": sample_user_data["password"],
        })

        response = await client.get("/api/v1/auth/me")
        assert response.status_code == 200
        data = response.json()
        assert data["email"] == sample_user_data["email"]
        assert data["full_name"] == sample_user_data["full_name"]

    @pytest.mark.asyncio
    async def test_logout(self, client: AsyncClient, sample_user_data):
        """Test logout clears cookies."""
        await client.post("/api/v1/auth/register", json=sample_user_data)
        await client.post("/api/v1/auth/login", json={
            "email": sample_user_data["email"],
            "password": sample_user_data["password"],
        })

        response = await client.post("/api/v1/auth/logout")
        assert response.status_code == 200

        # Verify cookies are cleared
        assert "access_token" not in response.cookies or response.cookies["access_token"] == ""
        assert "refresh_token" not in response.cookies or response.cookies["refresh_token"] == ""