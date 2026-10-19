"""document visibility

Adds documents.visibility ("public" | "private"). Existing documents without
an uploader (scraped website pages) become public; user uploads stay private.

Revision ID: 0002
Revises: 0001
Create Date: 2026-10-19 12:20:00
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "0002"
down_revision: Union[str, None] = "0001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "documents",
        sa.Column("visibility", sa.String(length=20), server_default="private", nullable=False),
    )
    op.create_index(op.f("ix_documents_visibility"), "documents", ["visibility"], unique=False)
    op.execute("UPDATE documents SET visibility = 'public' WHERE uploaded_by IS NULL")


def downgrade() -> None:
    op.drop_index(op.f("ix_documents_visibility"), table_name="documents")
    op.drop_column("documents", "visibility")
