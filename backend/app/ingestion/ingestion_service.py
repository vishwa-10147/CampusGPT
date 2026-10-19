# ==============================================================================
# CampusGPT Backend — Ingestion Service
# ==============================================================================
import asyncio
from typing import Optional, List
from uuid import UUID
from datetime import datetime

from sqlalchemy.ext.asyncio import AsyncSession

from app.ingestion.base_scraper import ScrapedDocument
from app.ingestion.mgit_scraper import MGITScraper
from app.services.document_service import DocumentService
from app.services.file_service import FileProcessingService
from app.services.embedding_service import get_embedding_service
from app.rag.chunker import split_text_recursive, clean_text, TextChunk
from app.repositories.document_repo import DocumentRepository, DocumentChunkRepository
from app.models.document import Document, DocumentChunk
from app.core.config import settings


class IngestionService:
    """Service for ingesting documents from various sources into RAG."""

    def __init__(self, session: AsyncSession):
        self.session = session
        self.doc_repo = DocumentRepository(session)
        self.chunk_repo = DocumentChunkRepository(session)
        self.doc_service = DocumentService(session)
        self.file_service = FileProcessingService(session)
        self.embedding = get_embedding_service()

    async def ingest_scraped_documents(
        self,
        documents: List[ScrapedDocument],
        source_name: str = "web",
    ) -> List[Document]:
        """
        Ingest scraped documents into the RAG system.

        Args:
            documents: List of scraped documents
            source_name: Source identifier (e.g., "mgit", "manual", "api")

        Returns:
            List of created Document records
        """
        created_docs = []

        for scraped in documents:
            try:
                # Create document record
                doc = await self.doc_repo.create(
                    filename=f"{source_name}_{scraped.url.replace('https://', '').replace('/', '_')[:100]}.txt",
                    original_name=scraped.title[:200],
                    mime_type="text/plain",
                    size_bytes=len(scraped.content.encode("utf-8")),
                    uploaded_by=None,  # System ingestion
                    status="processing",
                )

                # Process content: chunk + embed
                chunks = await self._process_content(doc.id, scraped.content)

                if chunks:
                    await self.doc_repo.update_status(doc.id, "ready")
                    doc.status = "ready"
                    doc.completed_at = datetime.utcnow()
                else:
                    await self.doc_repo.update_status(doc.id, "failed")
                    doc.status = "failed"

                # Commit per document so a long run keeps finished work
                await self.session.commit()
                created_docs.append(doc)

            except Exception as e:
                print(f"Error ingesting {scraped.url}: {e}")
                await self.session.rollback()

        return created_docs

    async def _process_content(self, document_id: UUID, content: str) -> List[DocumentChunk]:
        """Process text content: chunk, embed, store."""
        try:
            # Clean text
            clean_content = clean_text(content)
            print(f"Processing document {document_id}, content length: {len(clean_content)}")

            # Chunk text
            text_chunks = split_text_recursive(
                clean_content,
                chunk_size=settings.chunk_size,
                chunk_overlap=settings.chunk_overlap,
            )
            print(f"Created {len(text_chunks)} chunks")

            if not text_chunks:
                return []

            # Generate embeddings with retry for failed chunks
            texts = [chunk.content for chunk in text_chunks]
            print(f"Generating embeddings for {len(texts)} texts")
            embedding_response = await self.embedding.embed(texts)
            print(f"Embedding response type: {type(embedding_response)}")
            
            if embedding_response is None:
                raise ValueError("Embedding response is None")
            
            embeddings = embedding_response.embeddings
            print(f"Got {len(embeddings) if embeddings else 0} embeddings")

            # Check if we got valid embeddings
            if not embeddings or len(embeddings) != len(text_chunks):
                print(f"Warning: Got {len(embeddings) if embeddings else 0} embeddings for {len(text_chunks)} chunks")
                # Fill missing embeddings with zero vectors
                dimension = self.embedding.dimension if hasattr(self.embedding, 'dimension') else 768
                while len(embeddings) < len(text_chunks):
                    embeddings.append([0.0] * dimension)

            # Create chunk records - skip chunks with zero embeddings (indicates failure)
            chunk_records = []
            successful_chunks = 0
            for i, (text_chunk, embedding) in enumerate(zip(text_chunks, embeddings)):
                # Check if embedding is valid (not all zeros)
                if embedding and any(v != 0.0 for v in embedding):
                    chunk_record = DocumentChunk(
                        document_id=document_id,
                        content=text_chunk.content,
                        embedding=embedding,
                        chunk_index=i,
                        page_number=None,  # Web content doesn't have pages
                        chunk_metadata={
                            **text_chunk.metadata,
                            "char_count": len(text_chunk.content),
                            "source_type": "web",
                        },
                    )
                    chunk_records.append(chunk_record)
                    successful_chunks += 1
                else:
                    print(f"Warning: Skipping chunk {i} due to invalid embedding")

            if successful_chunks == 0:
                print(f"Error: No valid chunks for document {document_id}")
                return []

            print(f"Successfully created {successful_chunks}/{len(text_chunks)} chunks for document {document_id}")

            # Bulk insert
            created = await self.chunk_repo.bulk_create_chunks(chunk_records)
            return created
            
        except Exception as e:
            print(f"ERROR in _process_content for document {document_id}: {type(e).__name__}: {e}")
            import traceback
            traceback.print_exc()
            raise

    async def scrape_and_ingest_mgit(
        self,
        start_url: Optional[str] = None,
        max_pages: Optional[int] = None,
    ) -> dict:
        """
        Scrape MGIT website and ingest into RAG.

        Args:
            start_url: Starting URL (default: MGIT_BASE_URL)
            max_pages: Maximum pages to scrape (default: from settings)

        Returns:
            Ingestion result summary
        """
        start_url = start_url or settings.mgit_base_url
        max_pages = max_pages or settings.mgit_max_pages
        allowed_paths = settings.mgit_allowed_paths.split(",") if settings.mgit_allowed_paths else []
        delay = settings.mgit_scrape_delay_seconds

        print(f"Starting MGIT scrape: {start_url} (max {max_pages} pages)")

        async with MGITScraper(
            base_url=settings.mgit_base_url,
            delay_seconds=delay,
            max_pages=max_pages,
            allowed_paths=allowed_paths,
            respect_robots=settings.scraper_respect_robots_txt,
        ) as scraper:
            documents = await scraper.scrape(start_url)

        print(f"Scraped {len(documents)} pages from MGIT")

        if not documents:
            return {
                "status": "no_content",
                "message": "No content extracted from MGIT",
                "pages_scraped": 0,
                "documents_ingested": 0,
            }

        # Ingest into RAG
        created_docs = await self.ingest_scraped_documents(documents, "mgit")

        return {
            "status": "success",
            "pages_scraped": len(documents),
            "documents_ingested": len(created_docs),
            "source": "mgit",
            "timestamp": datetime.utcnow().isoformat(),
        }

    async def ingest_manual_text(
        self,
        title: str,
        content: str,
        source_name: str = "manual",
        metadata: Optional[dict] = None,
    ) -> Document:
        """Ingest manually provided text content."""
        scraped = ScrapedDocument(
            url=f"manual://{source_name}/{title.lower().replace(' ', '-')}",
            title=title,
            content=content,
            metadata=metadata or {},
        )

        docs = await self.ingest_scraped_documents([scraped], source_name)
        return docs[0] if docs else None


# Convenience function for scripts
async def run_mgit_ingestion(session: AsyncSession) -> dict:
    """Run full MGIT ingestion pipeline."""
    service = IngestionService(session)
    return await service.scrape_and_ingest_mgit()