# ==============================================================================
# CampusGPT Backend — Conversation Repository
# ==============================================================================
from datetime import datetime
from typing import Optional, Sequence
from uuid import UUID

from sqlalchemy import select, func, delete, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.conversation import Conversation
from app.models.message import Message
from app.repositories.base import BaseRepository


class ConversationRepository(BaseRepository[Conversation]):
    """Conversation repository with conversation-specific queries."""

    def __init__(self, session: AsyncSession):
        super().__init__(Conversation, session)

    async def get_user_conversations(
        self,
        user_id: UUID,
        *,
        offset: int = 0,
        limit: int = 20,
        include_deleted: bool = False,
    ) -> Sequence[Conversation]:
        """Get conversations for a user with pagination."""
        query = select(Conversation).where(Conversation.user_id == user_id)

        if not include_deleted:
            query = query.where(Conversation.deleted_at.is_(None))

        query = query.order_by(Conversation.updated_at.desc()).offset(offset).limit(limit)

        result = await self.session.execute(query)
        return result.scalars().all()

    async def count_user_conversations(self, user_id: UUID, include_deleted: bool = False) -> int:
        """Count user's conversations."""
        query = select(func.count(Conversation.id)).where(Conversation.user_id == user_id)

        if not include_deleted:
            query = query.where(Conversation.deleted_at.is_(None))

        result = await self.session.execute(query)
        return result.scalar_one()

    async def get_with_messages(
        self,
        conversation_id: UUID,
        user_id: UUID,
    ) -> Optional[Conversation]:
        """Get conversation with messages, verifying ownership."""
        result = await self.session.execute(
            select(Conversation)
            .where(
                Conversation.id == conversation_id,
                Conversation.user_id == user_id,
                Conversation.deleted_at.is_(None),
            )
            .options(selectinload(Conversation.messages))
        )
        return result.scalar_one_or_none()

    async def get_for_update(
        self,
        conversation_id: UUID,
        user_id: UUID,
    ) -> Optional[Conversation]:
        """Get conversation for update, verifying ownership."""
        result = await self.session.execute(
            select(Conversation).where(
                Conversation.id == conversation_id,
                Conversation.user_id == user_id,
                Conversation.deleted_at.is_(None),
            )
        )
        return result.scalar_one_or_none()

    async def soft_delete(self, conversation_id: UUID, user_id: UUID) -> bool:
        """Soft delete a conversation."""
        result = await self.session.execute(
            update(Conversation)
            .where(
                Conversation.id == conversation_id,
                Conversation.user_id == user_id,
                Conversation.deleted_at.is_(None),
            )
            .values(deleted_at=datetime.now(datetime.now().astimezone().tzinfo))
        )
        return result.rowcount > 0

    async def update_title(
        self,
        conversation_id: UUID,
        user_id: UUID,
        title: str,
    ) -> Optional[Conversation]:
        """Update conversation title."""
        conversation = await self.get_for_update(conversation_id, user_id)
        if not conversation:
            return None
        conversation.title = title
        await self.session.flush()
        await self.session.refresh(conversation)
        return conversation

    async def get_message_count(self, conversation_id: UUID) -> int:
        """Get message count for a conversation."""
        result = await self.session.execute(
            select(func.count(Message.id)).where(Message.conversation_id == conversation_id)
        )
        return result.scalar_one()

    async def get_last_message_preview(self, conversation_id: UUID) -> Optional[str]:
        """Get preview of last message."""
        result = await self.session.execute(
            select(Message.content)
            .where(Message.conversation_id == conversation_id)
            .order_by(Message.created_at.desc())
            .limit(1)
        )
        content = result.scalar_one_or_none()
        if content:
            return content[:100] + ("..." if len(content) > 100 else "")
        return None