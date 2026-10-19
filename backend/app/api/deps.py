# ==============================================================================
# CampusGPT Backend — API Dependencies
# ==============================================================================
from typing import Optional
from uuid import UUID

from fastapi import Depends, HTTPException, status, Cookie, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import get_token_subject, decode_token
from app.repositories.user_repo import UserRepository
from app.models.user import User
from app.services.auth_service import AuthService
from app.services.conversation_service import ConversationService
from app.services.document_service import DocumentService
from app.services.rag_service import RAGService


# ------------------------------------------------------------------------------
# Authentication Dependencies
# ------------------------------------------------------------------------------
async def get_current_user_id(
    access_token: Optional[str] = Cookie(None, alias="access_token"),
) -> UUID:
    """Extract and validate user ID from access token cookie."""
    if not access_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
        )

    user_id = get_token_subject(access_token, "access")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
        )

    return user_id


async def get_current_user(
    user_id: UUID = Depends(get_current_user_id),
    session: AsyncSession = Depends(get_db),
) -> User:
    """Get current user object."""
    user_repo = UserRepository(session)
    user = await user_repo.get_by_id(user_id)
    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or inactive",
        )
    return user


async def get_current_admin_user(
    user: User = Depends(get_current_user),
) -> User:
    """Require admin user."""
    if not user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required",
        )
    return user


async def get_optional_user(
    access_token: Optional[str] = Cookie(None, alias="access_token"),
    session: AsyncSession = Depends(get_db),
) -> Optional[User]:
    """Get current user if authenticated, otherwise None."""
    if not access_token:
        return None
    user_id = get_token_subject(access_token, "access")
    if not user_id:
        return None
    user_repo = UserRepository(session)
    return await user_repo.get_by_id(user_id)


# ------------------------------------------------------------------------------
# Service Dependencies
# ------------------------------------------------------------------------------
def get_auth_service(session: AsyncSession = Depends(get_db)) -> AuthService:
    return AuthService(session)


def get_conversation_service(session: AsyncSession = Depends(get_db)) -> ConversationService:
    return ConversationService(session)


def get_document_service(session: AsyncSession = Depends(get_db)) -> DocumentService:
    return DocumentService(session)


def get_rag_service(session: AsyncSession = Depends(get_db)) -> RAGService:
    return RAGService(session)