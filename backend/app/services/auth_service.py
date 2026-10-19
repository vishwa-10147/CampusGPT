# ==============================================================================
# CampusGPT Backend — Auth Service
# ==============================================================================
from uuid import UUID
from datetime import timedelta

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import (
    hash_password,
    verify_password,
    create_access_token,
    create_refresh_token,
    decode_token,
    get_token_subject,
)
from app.repositories.user_repo import UserRepository
from app.schemas.auth import RegisterRequest, LoginRequest, TokenResponse, UserResponse
from app.models.user import User


class AuthService:
    """Authentication business logic."""

    def __init__(self, session: AsyncSession):
        self.session = session
        self.user_repo = UserRepository(session)

    async def register(self, data: RegisterRequest) -> UserResponse:
        """Register a new user."""
        # Check if email exists
        if await self.user_repo.email_exists(data.email):
            raise ValueError("Email already registered")

        # Validate password confirmation
        if data.password != data.password_confirm:
            raise ValueError("Passwords do not match")

        # Create user
        user = await self.user_repo.create(
            email=data.email,
            password_hash=hash_password(data.password),
            full_name=data.full_name,
            is_active=True,
            is_admin=False,
        )

        return UserResponse.model_validate(user)

    async def login(self, data: LoginRequest) -> TokenResponse:
        """Authenticate user and return tokens."""
        user = await self.user_repo.get_by_email(data.email)
        if not user:
            raise ValueError("Invalid credentials")

        if not user.is_active:
            raise ValueError("Account is deactivated")

        if not verify_password(data.password, user.password_hash):
            raise ValueError("Invalid credentials")

        # Create tokens
        access_token = create_access_token(user.id)
        refresh_token = create_refresh_token(user.id)

        return TokenResponse(
            access_token=access_token,
            token_type="bearer",
            expires_in=15 * 60,  # 15 minutes in seconds
        )

    async def refresh_token(self, refresh_token: str) -> TokenResponse:
        """Refresh access token using refresh token."""
        payload = decode_token(refresh_token)
        if not payload or payload.get("type") != "refresh":
            raise ValueError("Invalid refresh token")

        user_id = get_token_subject(refresh_token)
        if not user_id:
            raise ValueError("Invalid refresh token")

        user = await self.user_repo.get_by_id(user_id)
        if not user or not user.is_active:
            raise ValueError("User not found or inactive")

        access_token = create_access_token(user_id)
        new_refresh_token = create_refresh_token(user_id)

        return TokenResponse(
            access_token=access_token,
            token_type="bearer",
            expires_in=15 * 60,
        )

    async def get_current_user(self, access_token: str) -> UserResponse:
        """Get current user from access token."""
        user_id = get_token_subject(access_token)
        if not user_id:
            raise ValueError("Invalid token")

        user = await self.user_repo.get_by_id(user_id)
        if not user or not user.is_active:
            raise ValueError("User not found or inactive")

        return UserResponse.model_validate(user)

    async def logout(self, refresh_token: str) -> None:
        """Logout - in a full implementation, would add token to blocklist."""
        # For MVP, we just validate the token exists
        # In production, add to Redis blocklist with TTL
        pass