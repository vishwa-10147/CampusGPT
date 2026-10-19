# ==============================================================================
# CampusGPT Backend — Vector Retriever
# ==============================================================================
from typing import List, Optional, Sequence
from uuid import UUID
from dataclasses import dataclass

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from pgvector.sqlalchemy import Vector

from app.models.document import DocumentChunk
from app.core.config import settings


@dataclass
class RetrievedChunk:
    """A retrieved chunk with similarity score."""
    chunk: DocumentChunk
    similarity: float


class VectorRetriever:
    """Vector similarity search using pgvector."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def search(
        self,
        query_embedding: List[float],
        *,
        top_k: int = None,
        similarity_threshold: float = None,
        document_ids: Optional[List[UUID]] = None,
    ) -> List[RetrievedChunk]:
        """
        Search for similar chunks using cosine similarity.
        
        Args:
            query_embedding: Query vector
            top_k: Number of results to return
            similarity_threshold: Minimum cosine similarity (0-1)
            document_ids: Optional filter to specific documents
        """
        top_k = top_k or settings.top_k_retrieval
        similarity_threshold = similarity_threshold or settings.similarity_threshold

        # Cosine similarity: 1 - cosine_distance
        # pgvector uses <=> for cosine distance
        similarity_expr = 1 - DocumentChunk.embedding.cosine_distance(query_embedding)

        query = (
            select(DocumentChunk, similarity_expr.label("similarity"))
            .where(DocumentChunk.embedding.is_not(None))
        )

        if document_ids:
            query = query.where(DocumentChunk.document_id.in_(document_ids))

        if similarity_threshold > 0:
            query = query.where(similarity_expr >= similarity_threshold)

        query = query.order_by(similarity_expr.desc()).limit(top_k)

        result = await self.session.execute(query)
        rows = result.all()

        return [
            RetrievedChunk(chunk=row[0], similarity=float(row[1]))
            for row in rows
        ]

    async def search_by_document(
        self,
        query_embedding: List[float],
        document_id: UUID,
        *,
        top_k: int = None,
        similarity_threshold: float = None,
    ) -> List[RetrievedChunk]:
        """Search within a specific document."""
        return await self.search(
            query_embedding,
            top_k=top_k,
            similarity_threshold=similarity_threshold,
            document_ids=[document_id],
        )

    async def get_chunk_count(self, document_id: UUID) -> int:
        """Get number of chunks with embeddings for a document."""
        result = await self.session.execute(
            select(func.count(DocumentChunk.id)).where(
                DocumentChunk.document_id == document_id,
                DocumentChunk.embedding.is_not(None),
            )
        )
        return result.scalar_one()