# ==============================================================================
# CampusGPT Backend — Conversation Model
# ==============================================================================
from datetime import datetime
from typing import Optional, List
from uuid import UUID as UUIDType

from sqlalchemy import DateTime, ForeignKey, String, Index
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDMixin


class Conversation(Base, UUIDMixin, TimestampMixin):
    """Chat conversation model."""

    __tablename__ = "conversations"

    user_id: Mapped[UUIDType] = mapped_column(
        UUID,
        ForeignKey("users.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    title: Mapped[str] = mapped_column(
        String(500),
        default="New Conversation",
        nullable=False,
    )
    deleted_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        index=True,
    )

    # Relationships
    user: Mapped["User"] = relationship(back_populates="conversations", lazy="selectin")
    messages: Mapped[List["Message"]] = relationship(
        back_populates="conversation",
        cascade="all, delete-orphan",
        lazy="selectin",
        order_by="Message.created_at",
    )

    # Table-level indexes
    __table_args__ = (
        Index("ix_conversations_user_id_created_at", "user_id", "created_at"),
        Index("ix_conversations_active", "user_id", "created_at", postgresql_where="deleted_at IS NULL"),
    )

    def __repr__(self) -> str:
        return f"<Conversation(id={self.id}, user_id={self.user_id}, title={self.title!r})>"