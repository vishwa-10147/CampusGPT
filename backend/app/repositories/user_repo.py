# ==============================================================================
# CampusGPT Backend — User Repository
# ==============================================================================
from typing import Optional, Sequence
from uuid import UUID

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User
from app.repositories.base import BaseRepository


class UserRepository(BaseRepository[User]):
    """User repository with user-specific queries."""

    def __init__(self, session: AsyncSession):
        super().__init__(User, session)

    async def get_by_email(self, email: str) -> Optional[User]:
        """Get user by email address."""
        result = await self.session.execute(
            select(User).where(User.email == email)
        )
        return result.scalar_one_or_none()

    async def get_by_id(self, user_id: UUID) -> Optional[User]:
        """Get user by ID."""
        return await self.get(user_id)

    async def email_exists(self, email: str) -> bool:
        """Check if email is already registered."""
        result = await self.session.execute(
            select(func.count(User.id)).where(User.email == email)
        )
        return result.scalar_one() > 0

    async def get_active_users(
        self,
        *,
        offset: int = 0,
        limit: int = 100,
    ) -> Sequence[User]:
        """Get active users with pagination."""
        result = await self.session.execute(
            select(User)
            .where(User.is_active == True)
            .offset(offset)
            .limit(limit)
        )
        return result.scalars().all()

    async def count_active_users(self) -> int:
        """Count active users."""
        result = await self.session.execute(
            select(func.count(User.id)).where(User.is_active == True)
        )
        return result.scalar_one()