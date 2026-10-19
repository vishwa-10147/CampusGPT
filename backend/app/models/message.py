# ==============================================================================
# CampusGPT Backend — Message Model
# ==============================================================================
from typing import Optional, List, Dict, Any
from uuid import UUID as UUIDType

from sqlalchemy import ForeignKey, Integer, String, Text, Index
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDMixin


class Message(Base, UUIDMixin, TimestampMixin):
    """Chat message model."""

    __tablename__ = "messages"

    conversation_id: Mapped[UUIDType] = mapped_column(
        UUID,
        ForeignKey("conversations.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    role: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
    )  # "user" | "assistant" | "system"
    content: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )
    sources: Mapped[Optional[List[Dict[str, Any]]]] = mapped_column(
        JSONB,
        nullable=True,
    )
    tokens_used: Mapped[Optional[int]] = mapped_column(
        Integer,
        nullable=True,
    )

    # Relationships
    conversation: Mapped["Conversation"] = relationship(back_populates="messages", lazy="selectin")

    # Table-level indexes
    __table_args__ = (
        Index("ix_messages_conversation_id_created_at", "conversation_id", "created_at"),
    )

    def __repr__(self) -> str:
        return f"<Message(id={self.id}, conversation_id={self.conversation_id}, role={self.role})>"