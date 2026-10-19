# ==============================================================================
# CampusGPT Backend — RAG Service
# ==============================================================================
from typing import List, Optional, AsyncGenerator
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.ai.base import ChatMessage
from app.rag.retriever import VectorRetriever, RetrievedChunk
from app.rag.citation import build_citations, citations_to_dict
from app.rag.prompts import build_rag_prompt, SYSTEM_PROMPT
from app.services.llm_service import get_llm_service
from app.services.embedding_service import get_embedding_service
from app.repositories.document_repo import DocumentRepository
from app.models.document import DocumentChunk


class RAGService:
    """Retrieval-Augmented Generation orchestration."""

    def __init__(self, session: AsyncSession):
        self.session = session
        self.retriever = VectorRetriever(session)
        self.llm = get_llm_service()
        self.embedding = get_embedding_service()
        self.doc_repo = DocumentRepository(session)

    async def answer_question(
        self,
        question: str,
        user_id: UUID,
        *,
        document_ids: Optional[List[UUID]] = None,
        stream: bool = True,
    ) -> AsyncGenerator[dict, None]:
        """
        Answer a question using RAG.
        
        Yields dicts with:
        - {"type": "token", "content": "..."} for streaming tokens
        - {"type": "sources", "sources": [...]} for citations
        - {"type": "done", "message_id": "...", "tokens_used": ...} when complete
        - {"type": "error", "error": "..."} on error
        """
        try:
            # 1. Embed the question
            query_embedding = await self.embedding.embed_single(question)

            # 2. Retrieve relevant chunks
            retrieved = await self.retriever.search(
                query_embedding,
                document_ids=document_ids,
            )

            # 3. Build citations
            citations = build_citations(retrieved)

            # 4. Build prompt
            prompt = build_rag_prompt(question, citations, SYSTEM_PROMPT)

            # 5. Generate answer
            messages = [
                ChatMessage(role="system", content=SYSTEM_PROMPT),
                ChatMessage(role="user", content=prompt),
            ]

            if stream:
                total_tokens = 0
                async for chunk in self.llm.chat_stream(messages):
                    if chunk.content:
                        yield {"type": "token", "content": chunk.content}
                    if chunk.done and chunk.tokens_used:
                        total_tokens = chunk.tokens_used

                # Send sources after streaming
                yield {"type": "sources", "sources": citations_to_dict(citations)}
                yield {"type": "done", "tokens_used": total_tokens}
            else:
                response = await self.llm.chat(messages)
                yield {"type": "token", "content": response.content}
                yield {"type": "sources", "sources": citations_to_dict(citations)}
                yield {"type": "done", "tokens_used": response.tokens_used}

        except Exception as e:
            yield {"type": "error", "error": str(e)}

    async def answer_question_simple(
        self,
        question: str,
        user_id: UUID,
        *,
        document_ids: Optional[List[UUID]] = None,
    ) -> dict:
        """Non-streaming answer for simpler use cases."""
        result = {"content": "", "sources": [], "tokens_used": 0}
        async for chunk in self.answer_question(question, user_id, document_ids=document_ids, stream=False):
            if chunk["type"] == "token":
                result["content"] = chunk["content"]
            elif chunk["type"] == "sources":
                result["sources"] = chunk["sources"]
            elif chunk["type"] == "done":
                result["tokens_used"] = chunk["tokens_used"]
            elif chunk["type"] == "error":
                raise Exception(chunk["error"])
        return result