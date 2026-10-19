# ==============================================================================
# CampusGPT Backend — Security Utilities
# ==============================================================================
from datetime import datetime, timedelta, timezone
from typing import Optional
from uuid import UUID

from jose import jwt, JWTError
from passlib.context import CryptContext
from pydantic import SecretStr

from app.core.config import settings


# ------------------------------------------------------------------------------
# Password Hashing (Argon2id)
# ------------------------------------------------------------------------------
pwd_context = CryptContext(
    schemes=["argon2"],
    deprecated="auto",
    argon2__time_cost=settings.argon2_time_cost,
    argon2__memory_cost=settings.argon2_memory_cost,
    argon2__parallelism=settings.argon2_parallelism,
    argon2__hash_len=32,
    argon2__salt_size=16,
)


def hash_password(password: str | SecretStr) -> str:
    """Hash a password using Argon2id."""
    if isinstance(password, SecretStr):
        return pwd_context.hash(password.get_secret_value())
    return pwd_context.hash(password)


def verify_password(plain_password: str | SecretStr, hashed_password: str) -> bool:
    """Verify a password against its hash."""
    if isinstance(plain_password, SecretStr):
        return pwd_context.verify(plain_password.get_secret_value(), hashed_password)
    return pwd_context.verify(plain_password, hashed_password)


# ------------------------------------------------------------------------------
# JWT Token Management
# ------------------------------------------------------------------------------
def create_access_token(subject: UUID, expires_delta: Optional[timedelta] = None) -> str:
    """Create a JWT access token."""
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=settings.access_token_expire_minutes)

    to_encode = {"sub": str(subject), "exp": expire, "type": "access"}
    return jwt.encode(to_encode, settings.secret_key, algorithm=settings.jwt_algorithm)


def create_refresh_token(subject: UUID, expires_delta: Optional[timedelta] = None) -> str:
    """Create a JWT refresh token."""
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(days=settings.refresh_token_expire_days)

    to_encode = {"sub": str(subject), "exp": expire, "type": "refresh"}
    return jwt.encode(to_encode, settings.secret_key, algorithm=settings.jwt_algorithm)


def create_email_verification_token(subject: UUID) -> str:
    """Create a signed, expiring token that proves control of the account's email."""
    expire = datetime.now(timezone.utc) + timedelta(hours=settings.email_verification_expire_hours)
    to_encode = {"sub": str(subject), "exp": expire, "type": "verify_email"}
    return jwt.encode(to_encode, settings.secret_key, algorithm=settings.jwt_algorithm)


def decode_token(token: str) -> Optional[dict]:
    """Decode and validate a JWT token. Returns payload or None if invalid."""
    try:
        payload = jwt.decode(token, settings.secret_key, algorithms=[settings.jwt_algorithm])
        return payload
    except JWTError:
        return None


def get_token_subject(token: str, token_type: Optional[str] = None) -> Optional[UUID]:
    """Extract the subject (user ID) from a token, optionally requiring its type."""
    payload = decode_token(token)
    if not payload:
        return None
    if token_type and payload.get("type") != token_type:
        return None
    try:
        return UUID(payload.get("sub"))
    except (ValueError, TypeError):
        return None


def is_token_expired(token: str) -> bool:
    """Check if a token is expired without raising exceptions."""
    payload = decode_token(token)
    if not payload:
        return True
    exp = payload.get("exp")
    if not exp:
        return True
    return datetime.now(timezone.utc) >= datetime.fromtimestamp(exp, tz=timezone.utc)