# ==============================================================================
# CampusGPT Backend — Conversation Service
# ==============================================================================
from typing import Optional, Sequence
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories.conversation_repo import ConversationRepository
from app.repositories.message_repo import MessageRepository
from app.schemas.conversation import ConversationCreate, ConversationUpdate, ConversationResponse, ConversationListResponse
from app.schemas.message import MessageResponse


class ConversationService:
    """Conversation business logic."""

    def __init__(self, session: AsyncSession):
        self.session = session
        self.conv_repo = ConversationRepository(session)
        self.msg_repo = MessageRepository(session)

    async def create_conversation(self, user_id: UUID, data: ConversationCreate) -> ConversationResponse:
        """Create a new conversation."""
        title = data.title or "New Conversation"
        conversation = await self.conv_repo.create(
            user_id=user_id,
            title=title,
        )
        return ConversationResponse.model_validate(conversation)

    async def get_conversation(self, conversation_id: UUID, user_id: UUID) -> Optional[ConversationResponse]:
        """Get a conversation with messages."""
        conversation = await self.conv_repo.get_with_messages(conversation_id, user_id)
        if not conversation:
            return None

        messages = [
            MessageResponse.model_validate(msg) for msg in conversation.messages
        ]
        return ConversationResponse(
            id=conversation.id,
            user_id=conversation.user_id,
            title=conversation.title,
            created_at=conversation.created_at,
            updated_at=conversation.updated_at,
            deleted_at=conversation.deleted_at,
            message_count=len(messages),
            last_message_preview=messages[-1].content[:100] if messages else None,
        )

    async def list_conversations(
        self,
        user_id: UUID,
        *,
        page: int = 1,
        page_size: int = 20,
    ) -> ConversationListResponse:
        """List user's conversations with pagination."""
        offset = (page - 1) * page_size

        conversations = await self.conv_repo.get_user_conversations(
            user_id, offset=offset, limit=page_size
        )
        total = await self.conv_repo.count_user_conversations(user_id)

        # Build response with message counts and previews
        conv_responses = []
        for conv in conversations:
            msg_count = await self.conv_repo.get_message_count(conv.id)
            preview = await self.conv_repo.get_last_message_preview(conv.id)
            conv_responses.append(ConversationResponse(
                id=conv.id,
                user_id=conv.user_id,
                title=conv.title,
                created_at=conv.created_at,
                updated_at=conv.updated_at,
                deleted_at=conv.deleted_at,
                message_count=msg_count,
                last_message_preview=preview,
            ))

        return ConversationListResponse(
            conversations=conv_responses,
            total=total,
            page=page,
            page_size=page_size,
            total_pages=(total + page_size - 1) // page_size,
        )

    async def update_conversation(
        self,
        conversation_id: UUID,
        user_id: UUID,
        data: ConversationUpdate,
    ) -> Optional[ConversationResponse]:
        """Update conversation title."""
        conversation = await self.conv_repo.update_title(conversation_id, user_id, data.title)
        if not conversation:
            return None
        return ConversationResponse.model_validate(conversation)

    async def delete_conversation(self, conversation_id: UUID, user_id: UUID) -> bool:
        """Soft delete a conversation."""
        return await self.conv_repo.soft_delete(conversation_id, user_id)

    async def add_message(
        self,
        conversation_id: UUID,
        user_id: UUID,
        role: str,
        content: str,
        sources: Optional[list] = None,
        tokens_used: Optional[int] = None,
    ) -> MessageResponse:
        """Add a message to a conversation (verifies ownership)."""
        # Verify conversation ownership
        conversation = await self.conv_repo.get_for_update(conversation_id, user_id)
        if not conversation:
            raise ValueError("Conversation not found or access denied")

        message = await self.msg_repo.create_message(
            conversation_id=conversation_id,
            role=role,
            content=content,
            sources=sources,
            tokens_used=tokens_used,
        )
        return MessageResponse.model_validate(message)

    async def get_messages(
        self,
        conversation_id: UUID,
        user_id: UUID,
        *,
        offset: int = 0,
        limit: int = 100,
    ) -> Sequence[MessageResponse]:
        """Get messages for a conversation."""
        # Verify ownership
        conversation = await self.conv_repo.get_for_update(conversation_id, user_id)
        if not conversation:
            raise ValueError("Conversation not found or access denied")

        messages = await self.msg_repo.get_conversation_messages(
            conversation_id, offset=offset, limit=limit
        )
        return [MessageResponse.model_validate(m) for m in messages]