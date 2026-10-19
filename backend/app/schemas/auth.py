# ==============================================================================
# CampusGPT Backend — Auth Schemas
# ==============================================================================
from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field, ConfigDict


class RegisterRequest(BaseModel):
    """User registration request."""
    email: EmailStr = Field(..., description="User's email address")
    password: str = Field(..., min_length=8, max_length=128, description="Password (min 8 chars)")
    password_confirm: str = Field(..., description="Password confirmation")
    full_name: str = Field(..., min_length=1, max_length=255, description="Full name")

    model_config = ConfigDict(str_strip_whitespace=True)


class LoginRequest(BaseModel):
    """User login request."""
    email: EmailStr = Field(..., description="User's email address")
    password: str = Field(..., description="Password")

    model_config = ConfigDict(str_strip_whitespace=True)


class TokenResponse(BaseModel):
    """Token response (access token in body, refresh in HttpOnly cookie)."""
    access_token: str = Field(..., description="JWT access token")
    token_type: str = Field(default="bearer", description="Token type")
    expires_in: int = Field(..., description="Access token lifetime in seconds")


class RefreshRequest(BaseModel):
    """Token refresh request (refresh token from HttpOnly cookie)."""
    pass  # Token read from cookie


class UserResponse(BaseModel):
    """User profile response."""
    id: UUID
    email: str
    full_name: str
    is_active: bool
    is_admin: bool
    email_verified: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class VerifyEmailRequest(BaseModel):
    """Email verification (token from the emailed link)."""
    token: str


class ResendVerificationRequest(BaseModel):
    """Request a new verification email."""
    email: EmailStr


class MessageResponse(BaseModel):
    """Generic message response."""
    message: str