# ==============================================================================
# CampusGPT Backend — Message Repository
# ==============================================================================
from typing import Optional, Sequence
from uuid import UUID

from sqlalchemy import select, func, delete
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.message import Message
from app.repositories.base import BaseRepository


class MessageRepository(BaseRepository[Message]):
    """Message repository with message-specific queries."""

    def __init__(self, session: AsyncSession):
        super().__init__(Message, session)

    async def get_conversation_messages(
        self,
        conversation_id: UUID,
        *,
        offset: int = 0,
        limit: int = 100,
    ) -> Sequence[Message]:
        """Get messages for a conversation with pagination."""
        result = await self.session.execute(
            select(Message)
            .where(Message.conversation_id == conversation_id)
            .order_by(Message.created_at.asc())
            .offset(offset)
            .limit(limit)
        )
        return result.scalars().all()

    async def count_conversation_messages(self, conversation_id: UUID) -> int:
        """Count messages in a conversation."""
        result = await self.session.execute(
            select(func.count(Message.id)).where(Message.conversation_id == conversation_id)
        )
        return result.scalar_one()

    async def create_message(
        self,
        conversation_id: UUID,
        role: str,
        content: str,
        sources: Optional[list] = None,
        tokens_used: Optional[int] = None,
    ) -> Message:
        """Create a new message."""
        return await self.create(
            conversation_id=conversation_id,
            role=role,
            content=content,
            sources=sources,
            tokens_used=tokens_used,
        )

    async def delete_conversation_messages(self, conversation_id: UUID) -> int:
        """Delete all messages in a conversation."""
        result = await self.session.execute(
            delete(Message).where(Message.conversation_id == conversation_id)
        )
        return result.rowcount