# CampusGPT — Phase 1: Professional MVP Plan

## 1. Product Requirements Document (PRD)

### 1.1 Product Vision
CampusGPT is an institutional AI assistant platform for colleges that provides students, faculty, and administrators with a secure, ChatGPT-like interface to access academic assistance, college information, research resources, and institutional services through Retrieval-Augmented Generation (RAG) over authorized college documents.

### 1.2 Target Users (MVP)
| User Type | Description | MVP Access |
|-----------|-------------|------------|
| **Student** | Enrolled students seeking academic help, college info | Full chat + document upload (if permitted) + conversation history |
| **Faculty** | Teaching staff accessing resources | Same as student (role differentiation in Phase 3) |
| **Admin** | College administrators managing knowledge base | Admin panel for document management + all student features |

### 1.3 Core Use Cases (MVP)
1. **UC-01**: User registers and authenticates securely
2. **UC-02**: User starts a new conversation with the AI assistant
3. **UC-03**: User asks questions about the college and receives grounded answers
4. **UC-04**: User uploads authorized documents (PDF, TXT) for indexing
5. **UC-05**: User asks questions about uploaded documents with source citations
6. **UC-06**: User views conversation history and resumes previous chats
7. **UC-07**: User deletes conversations (per retention policy)
8. **UC-08**: Admin manages knowledge base documents via admin interface
9. **UC-09**: System handles errors gracefully (model failures, invalid uploads)
10. **UC-10**: AI acknowledges when it cannot find evidence in knowledge base

### 1.4 MVP Scope — Explicit Non-Goals
| Non-Goal | Reason | Phase |
|----------|--------|-------|
| Multi-agent orchestration | Complexity | Future |
| Attendance/exam/payment integrations | Requires institutional APIs | Phase 3 |
| Role-based access control (beyond basic admin/user) | Security foundation first | Phase 3 |
| Alumni directory ingestion | Policy/legal review needed | Phase 2 |
| Custom model training | Cost/complexity | Never (use APIs) |
| Microservices architecture | Premature optimization | Never (modular monolith) |
| Real-time collaboration | Not core to MVP | Future |
| Voice/audio interface | Accessibility later | Future |
| Multi-language support | English-first MVP | Future |

### 1.5 Acceptance Criteria (MVP Complete When...)
- [ ] New user can register, verify email, and authenticate
- [ ] Users cannot access another user's private conversations (isolation enforced in DB + API)
- [ ] Chat interface works on mobile (375px), tablet (768px), desktop (1440px)
- [ ] Configured LLM produces streaming responses
- [ ] Uploaded documents (PDF/TXT) are indexed and searchable within 30s
- [ ] Answers include verifiable source citations with page/chunk references
- [ ] Invalid uploads (wrong type, too large, corrupted) are rejected safely
- [ ] Model failures show user-friendly error with retry option
- [ ] Data persists across container restarts (PostgreSQL + pgvector)
- [ ] Automated tests pass (unit + integration + e2e for core flows)
- [ ] Fresh developer can clone repo and run with `docker compose up` per README

---

## 2. Architecture Overview

### 2.1 High-Level Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              CAMPUSGPT MVP ARCHITECTURE                       │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  ┌──────────────┐     HTTPS/WSS      ┌──────────────┐                       │
│  │   FRONTEND   │ ◄─────────────────► │   BACKEND    │                       │
│  │  (React +    │   REST + SSE       │  (FastAPI)   │                       │
│  │  TypeScript) │                    │              │                       │
│  └──────────────┘                    └──────┬───────┘                       │
│         │                                   │                               │
│         │                                   ▼                               │
│         │                          ┌──────────────────┐                     │
│         │                          │  POSTGRESQL      │                     │
│         │                          │  + pgvector      │                     │
│         │                          │  (Primary DB)    │                     │
│         │                          └────────┬─────────┘                     │
│         │                                   │                               │
│         │              ┌────────────────────┼────────────────────┐          │
│         │              ▼                    ▼                    ▼          │
│         │  ┌─────────────────┐    ┌─────────────────┐    ┌─────────────┐  │
│         │  │  LLM PROVIDER   │    │ EMBEDDING       │    │  FILE       │  │
│         │  │  (OpenAI/       │    │ SERVICE         │    │  STORAGE    │  │
│         │  │   Anthropic/    │    │ (OpenAI/        │    │  (Local/    │  │
│         │  │   Local)        │    │  Local)         │    │   S3)       │  │
│         │  └─────────────────┘    └─────────────────┘    └─────────────┘  │
│         │                                                                   │
│         └───────────────────────────────────────────────────────────────────┘
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 2.2 Component Breakdown

#### Frontend (`/frontend`)
```
src/
├── components/           # Reusable UI components
│   ├── ui/              # Base components (Button, Input, Modal, etc.)
│   ├── chat/            # Chat-specific (MessageBubble, StreamingResponse, CitationCard)
│   ├── layout/          # Sidebar, Header, Footer, ResponsiveNav
│   └── forms/           # LoginForm, RegisterForm, UploadForm
├── pages/               # Route-level components
│   ├── Login.tsx
│   ├── Register.tsx
│   ├── Chat.tsx         # Main chat interface
│   ├── ConversationList.tsx
│   ├── Settings.tsx
│   └── Admin/
│       └── Documents.tsx
├── features/            # Feature-specific logic (auth, chat, documents)
├── hooks/               # Custom React hooks (useAuth, useChat, useConversations)
├── services/            # API clients (api.ts, auth.ts, chat.ts, documents.ts)
├── types/               # TypeScript interfaces
├── utils/               # Helpers (date formatting, markdown rendering)
└── styles/              # Global CSS, Tailwind config
```

#### Backend (`/backend/app`)
```
app/
├── api/                 # FastAPI route handlers (thin)
│   ├── v1/
│   │   ├── auth.py
│   │   ├── conversations.py
│   │   ├── messages.py
│   │   ├── documents.py
│   │   └── admin.py
│   └── deps.py          # Dependency injection (auth, db, services)
├── core/                # Configuration, security, constants
│   ├── config.py        # Pydantic Settings from env vars
│   ├── security.py      # Password hashing, JWT, password validation
│   └── constants.py
├── models/              # SQLAlchemy ORM models
│   ├── user.py
│   ├── conversation.py
│   ├── message.py
│   ├── document.py
│   └── document_chunk.py
├── schemas/             # Pydantic request/response models
│   ├── auth.py
│   ├── conversation.py
│   ├── message.py
│   └── document.py
├── services/            # Business logic (thick)
│   ├── auth_service.py
│   ├── conversation_service.py
│   ├── message_service.py
│   ├── document_service.py
│   ├── llm_service.py   # Provider-agnostic LLM interface
│   ├── embedding_service.py
│   ├── rag_service.py   # Retrieval + generation orchestration
│   └── file_service.py
├── repositories/        # Data access layer
│   ├── user_repo.py
│   ├── conversation_repo.py
│   ├── message_repo.py
│   └── document_repo.py
├── ai/                  # AI provider adapters
│   ├── base.py          # Abstract interfaces
│   ├── openai_adapter.py
│   ├── anthropic_adapter.py
│   └── local_adapter.py
├── rag/                 # RAG pipeline components
│   ├── chunker.py       # Text splitting strategies
│   ├── retriever.py     # Vector search + filtering
│   ├── citation.py      # Citation building
│   └── prompts.py       # System prompts, templates
└── tests/               # Backend tests (mirrors app structure)
```

### 2.3 Key Design Decisions

| Decision | Rationale | Alternative Considered |
|----------|-----------|------------------------|
| **Modular monolith** | Simple deployment, clear boundaries, can split later | Microservices (too complex for MVP) |
| **FastAPI + SQLAlchemy 2.0** | Async support, type safety, great DX, pgvector native | Django (heavier), Flask (less structured) |
| **React + TypeScript + Vite** | Industry standard, fast HMR, type safety | Next.js (SSR not needed for chat app) |
| **Tailwind CSS** | Rapid UI dev, consistent design system, small bundle | CSS Modules (more boilerplate) |
| **Provider-agnostic LLM interface** | Swap providers without rewriting app logic | Direct OpenAI SDK coupling |
| **pgvector in PostgreSQL** | Single DB, ACID, mature, good enough for MVP | Pinecone/Weaviate (external dependency) |
| **SSE for streaming** | Simple, works over HTTP/2, no WebSocket complexity | WebSockets (more complex auth/connection mgmt) |
| **JWT in HttpOnly cookies** | CSRF-resistant, secure, mobile-friendly | LocalStorage (XSS vulnerable) |

---

## 3. Database Schema (ER Diagram)

### 3.1 Entity Relationship Diagram

```
┌─────────────┐       ┌──────────────────┐       ┌─────────────┐
│   users     │       │  conversations   │       │  messages   │
├─────────────┤       ├──────────────────┤       ├─────────────┤
│ id (PK)     │◄──────│ id (PK)          │◄──────│ id (PK)     │
│ email       │       │ user_id (FK)     │       │ conv_id(FK) │
│ password_hash│      │ title            │       │ role        │
│ full_name   │       │ created_at       │       │ content     │
│ is_active   │       │ updated_at       │       │ sources     │
│ is_admin    │       │ deleted_at       │       │ tokens_used │
│ created_at  │       └──────────────────┘       │ created_at  │
│ updated_at  │                                  └─────────────┘
└─────────────┘
       │
       │ 1:N (admin only for MVP)
       ▼
┌─────────────┐       ┌─────────────┐       ┌──────────────────┐
│  documents  │       │document_chunks│      │  ingestion_jobs  │
├─────────────┤       ├─────────────┤       ├──────────────────┤
│ id (PK)     │◄──────│ id (PK)     │       │ id (PK)          │
│ filename    │       │ doc_id (FK) │       │ document_id (FK) │
│ original_name│      │ content     │       │ status           │
│ mime_type   │       │ embedding   │       │ progress         │
│ size_bytes  │       │ (vector)    │       │ error_message    │
│ uploaded_by │       │ chunk_index │       │ started_at       │
│ status      │       │ page_number │       │ completed_at     │
│ created_at  │       │ metadata    │       └──────────────────┘
└─────────────┘       └─────────────┘
```

### 3.2 Table Definitions (SQLAlchemy Models)

```python
# users table
class User(Base):
    __tablename__ = "users"
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    full_name: Mapped[str] = mapped_column(String(255), nullable=False)
    is_active: Mapped[bool] = mapped_column(default=True, nullable=False)
    is_admin: Mapped[bool] = mapped_column(default=False, nullable=False)  # Simple MVP admin flag
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

# conversations table
class Conversation(Base):
    __tablename__ = "conversations"
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False)
    title: Mapped[str] = mapped_column(String(500), default="New Conversation")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    deleted_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True, index=True)
    
    user: Mapped["User"] = relationship(back_populates="conversations")
    messages: Mapped[List["Message"]] = relationship(back_populates="conversation", cascade="all, delete-orphan")

# messages table
class Message(Base):
    __tablename__ = "messages"
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    conversation_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("conversations.id", ondelete="CASCADE"), index=True, nullable=False)
    role: Mapped[str] = mapped_column(String(20), nullable=False)  # "user" | "assistant" | "system"
    content: Mapped[str] = mapped_column(Text, nullable=False)
    sources: Mapped[Optional[List[Dict]]] = mapped_column(JSONB, nullable=True)  # Citation data
    tokens_used: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    
    conversation: Mapped["Conversation"] = relationship(back_populates="messages")

# documents table
class Document(Base):
    __tablename__ = "documents"
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    filename: Mapped[str] = mapped_column(String(255), nullable=False)  # Stored filename
    original_name: Mapped[str] = mapped_column(String(255), nullable=False)  # User's filename
    mime_type: Mapped[str] = mapped_column(String(100), nullable=False)
    size_bytes: Mapped[int] = mapped_column(BigInteger, nullable=False)
    uploaded_by: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    status: Mapped[str] = mapped_column(String(30), default="pending", index=True)  # pending, processing, ready, failed
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    
    uploader: Mapped["User"] = relationship()
    chunks: Mapped[List["DocumentChunk"]] = relationship(back_populates="document", cascade="all, delete-orphan")

# document_chunks table (with pgvector)
class DocumentChunk(Base):
    __tablename__ = "document_chunks"
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    document_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("documents.id", ondelete="CASCADE"), index=True, nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    embedding: Mapped[List[float]] = mapped_column(Vector(1536), nullable=True)  # OpenAI text-embedding-3-small
    chunk_index: Mapped[int] = mapped_column(Integer, nullable=False)
    page_number: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    metadata: Mapped[Dict] = mapped_column(JSONB, default=dict, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    
    document: Mapped["Document"] = relationship(back_populates="chunks")

# ingestion_jobs table (async processing tracking)
class IngestionJob(Base):
    __tablename__ = "ingestion_jobs"
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    document_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("documents.id", ondelete="CASCADE"), index=True, nullable=False)
    status: Mapped[str] = mapped_column(String(30), default="queued", index=True)  # queued, processing, completed, failed
    progress: Mapped[int] = mapped_column(Integer, default=0)  # 0-100
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    started_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
```

### 3.3 Indexes & Constraints

```sql
-- Critical indexes for performance
CREATE INDEX ix_conversations_user_id_created_at ON conversations(user_id, created_at DESC);
CREATE INDEX ix_messages_conversation_id_created_at ON messages(conversation_id, created_at);
CREATE INDEX ix_documents_uploaded_by_status ON documents(uploaded_by, status);
CREATE INDEX ix_document_chunks_document_id_chunk_index ON document_chunks(document_id, chunk_index);

-- pgvector HNSW index for similarity search (created after data exists)
CREATE INDEX ix_document_chunks_embedding_hnsw ON document_chunks 
USING hnsw (embedding vector_cosine_ops) WITH (m = 16, ef_construction = 64);

-- Soft delete filter (partial index)
CREATE INDEX ix_conversations_active ON conversations(user_id, created_at DESC) 
WHERE deleted_at IS NULL;
```

---

## 4. API Specification (OpenAPI 3.0)

### 4.1 Authentication Endpoints

| Method | Path | Description | Auth |
|--------|------|-------------|------|
| POST | `/api/v1/auth/register` | Register new user | None |
| POST | `/api/v1/auth/login` | Login, set HttpOnly cookie | None |
| POST | `/api/v1/auth/logout` | Logout, clear cookie | Required |
| GET | `/api/v1/auth/me` | Get current user profile | Required |
| POST | `/api/v1/auth/refresh` | Refresh access token | Refresh token |

### 4.2 Conversation Endpoints

| Method | Path | Description | Auth |
|--------|------|-------------|------|
| GET | `/api/v1/conversations` | List user's conversations (paginated) | Required |
| POST | `/api/v1/conversations` | Create new conversation | Required |
| GET | `/api/v1/conversations/{id}` | Get conversation with messages | Required |
| PATCH | `/api/v1/conversations/{id}` | Update title | Required |
| DELETE | `/api/v1/conversations/{id}` | Soft delete conversation | Required |

### 4.3 Message Endpoints

| Method | Path | Description | Auth |
|--------|------|-------------|------|
| POST | `/api/v1/conversations/{id}/messages` | Send message, get streaming response | Required |
| POST | `/api/v1/conversations/{id}/messages/{msg_id}/retry` | Retry failed assistant message | Required |

### 4.4 Document Endpoints

| Method | Path | Description | Auth |
|--------|------|-------------|------|
| POST | `/api/v1/documents/upload` | Upload document (multipart/form-data) | Required |
| GET | `/api/v1/documents` | List user's documents (paginated) | Required |
| GET | `/api/v1/documents/{id}` | Get document status & metadata | Required |
| DELETE | `/api/v1/documents/{id}` | Delete document & chunks | Required |
| GET | `/api/v1/documents/{id}/chunks` | List document chunks (admin) | Admin |

### 4.5 Admin Endpoints (MVP: is_admin flag)

| Method | Path | Description | Auth |
|--------|------|-------------|------|
| GET | `/api/v1/admin/documents` | All documents with filters | Admin |
| PATCH | `/api/v1/admin/documents/{id}` | Update document status/metadata | Admin |
| GET | `/api/v1/admin/stats` | System stats (users, docs, conversations) | Admin |

### 4.6 Request/Response Examples

**POST `/api/v1/conversations/{id}/messages`**
```json
// Request
{
  "content": "What is the college's academic calendar for 2024-25?",
  "stream": true
}

// Response (SSE stream)
event: token
data: "The academic calendar for 2024-25..."

event: token
data: " includes fall semester starting..."

event: sources
data: [{"document_id": "uuid", "filename": "calendar.pdf", "page": 3, "chunk_index": 5, "text": "Fall 2024: Aug 26 - Dec 13"}]

event: done
data: {"message_id": "uuid", "tokens_used": 245}
```

---

## 5. Security Model (MVP)

### 5.1 Authentication
- **Password hashing**: Argon2id (via `passlib`) — memory-hard, resistant to GPU cracking
- **JWT tokens**: Access token (15min) + Refresh token (7d) in HttpOnly, Secure, SameSite=Strict cookies
- **Token rotation**: Refresh token rotated on each use; old token revoked
- **Session revocation**: Server-side blocklist for logout/compromise (Redis or DB table)

### 5.2 Authorization
- **MVP**: Simple `is_admin` boolean on User model
- **Conversation ownership**: Every API checks `conversation.user_id == current_user.id`
- **Document ownership**: Users see only their uploads; admins see all

### 5.3 Input Validation & Sanitization
- **Pydantic models** on all request bodies (strict=True)
- **File uploads**: MIME type validation (magic bytes), size limit (10MB), extension allowlist (.pdf, .txt, .md)
- **Path traversal**: Secure filename generation (UUID + original extension)
- **SQL injection**: SQLAlchemy ORM (parameterized queries)
- **XSS**: React auto-escapes; markdown rendering with `dompurify`

### 5.4 Rate Limiting
- **Auth endpoints**: 5 requests/minute per IP
- **Chat endpoints**: 30 requests/minute per user
- **Upload endpoints**: 10 uploads/hour per user
- Implementation: `slowapi` (FastAPI middleware)

### 5.5 Security Headers (via `secure` middleware)
```
Content-Security-Policy: default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'
X-Frame-Options: DENY
X-Content-Type-Options: nosniff
Referrer-Policy: strict-origin-when-cross-origin
Permissions-Policy: camera=(), microphone=(), geolocation=()
Strict-Transport-Security: max-age=31536000; includeSubDomains (production only)
```

### 5.6 Secrets Management
- **Development**: `.env` file (gitignored)
- **Production**: Docker secrets / environment variables / vault
- **Never committed**: API keys, DB passwords, JWT secrets

---

## 6. UI/UX Design Plan

### 6.1 Design System
- **Colors**: Professional blue primary (#2563EB), neutral grays, semantic colors (success, warning, error)
- **Typography**: Inter font family, consistent scale (xs-4xl)
- **Spacing**: 4px base unit, Tailwind spacing scale
- **Border radius**: 6px (cards), 8px (modals), 9999px (pills)
- **Shadows**: 3 elevation levels
- **Transitions**: 150ms ease-out

### 6.2 Responsive Breakpoints
| Breakpoint | Width | Layout |
|------------|-------|--------|
| Mobile | < 640px | Stacked: Conversation list as drawer, full-width chat |
| Tablet | 640-1023px | Collapsible sidebar, chat area |
| Desktop | ≥ 1024px | Persistent sidebar (280px), chat area |

### 6.3 Key Pages & Components

#### Login / Register
- Centered card, 400px max width
- Email + password + confirm (register)
- Validation inline, submit loading state
- Link to switch between login/register
- "Forgot password" (Phase 3)

#### Chat Home (`/chat`)
```
┌─────────────────────────────────────────────────────────────┐
│ Header: CampusGPT logo | User menu (settings, logout)       │
├──────────────┬──────────────────────────────────────────────┤
│              │                                              │
│  SIDEBAR     │  CHAT AREA                                   │
│  (280px)     │                                              │
│              │  ┌────────────────────────────────────────┐  │
│  [New Chat]  │  │ Welcome message / Empty state          │  │
│              │  ├────────────────────────────────────────┤  │
│  Conversation│  │ Message 1 (user)                       │  │
│  List        │  │ Message 2 (assistant) + citations 📎   │  │
│              │  │ Message 3 (user)                       │  │
│  - Title     │  │ Message 4 (assistant streaming...) █   │  │
│  - Preview   │  ├────────────────────────────────────────┤  │
│  - Time      │  │ Composer: [Input..............] [Send] │  │
│  - Delete 🗑 │  │        [Attach] [Model] [Settings]     │  │
│              │  └────────────────────────────────────────┘  │
└──────────────┴──────────────────────────────────────────────┘
```

#### Message Component
- User: right-aligned, blue bubble
- Assistant: left-aligned, gray bubble
- Streaming: character-by-character with cursor
- Citations: expandable chips below message showing source + snippet
- Error: red banner with "Retry" button

#### Document Upload
- Drag-and-drop zone + file picker
- Progress bar during upload
- Status badges: Pending → Processing → Ready / Failed
- Error toast with retry

#### Admin Documents Page
- Table: Filename | Status | Uploaded By | Date | Actions
- Filter by status, search by name
- Bulk delete, re-process

### 6.4 Accessibility (WCAG 2.1 AA)
- Semantic HTML, ARIA labels
- Keyboard navigation (Tab, Enter, Escape)
- Focus visible outlines
- Color contrast ≥ 4.5:1
- Screen reader announcements for streaming content
- Reduced motion support

---

## 7. Phased Implementation Backlog

### Sprint 1: Foundation (Week 1)
| Task | Dependencies | Est. Hours |
|------|--------------|------------|
| Initialize monorepo with Docker Compose | None | 4 |
| PostgreSQL + pgvector container setup | Docker | 2 |
| Backend: Config, security, database connection | Docker | 4 |
| Backend: User model, migration, auth service | DB | 6 |
| Backend: Auth API (register, login, logout, me) | Auth service | 4 |
| Frontend: Vite + React + TS + Tailwind setup | None | 3 |
| Frontend: Auth pages, auth context, API client | Backend auth API | 6 |
| **Integration test: Register → Login → Me** | Both | 2 |

### Sprint 2: Conversations & Chat Core (Week 2)
| Task | Dependencies | Est. Hours |
|------|--------------|------------|
| Backend: Conversation/Message models + migrations | Sprint 1 | 4 |
| Backend: Conversation CRUD API | Models | 4 |
| Backend: LLM service abstraction + OpenAI adapter | Config | 6 |
| Backend: Chat endpoint (non-streaming first) | LLM service | 4 |
| Frontend: Chat page layout, sidebar, conversation list | Sprint 1 | 6 |
| Frontend: Message components, composer | Chat page | 4 |
| Frontend: Chat hook + API integration | Backend chat API | 4 |
| **Integration test: New chat → Send message → Receive response** | Both | 3 |

### Sprint 3: Streaming & Polish (Week 3)
| Task | Dependencies | Est. Hours |
|------|--------------|------------|
| Backend: SSE streaming endpoint | Chat endpoint | 4 |
| Backend: Token usage tracking, error handling | Streaming | 3 |
| Frontend: Streaming response rendering | SSE endpoint | 4 |
| Frontend: Loading, error, retry states | Streaming | 3 |
| Frontend: Conversation persistence, deletion | Conv API | 3 |
| **E2E test: Full chat flow with streaming** | Both | 2 |

### Sprint 4: Document Upload & RAG (Week 4)
| Task | Dependencies | Est. Hours |
|------|--------------|------------|
| Backend: Document/Chunk models + migrations | Sprint 1 | 3 |
| Backend: File upload endpoint + validation | Models | 4 |
| Backend: Text extraction (PyPDF2, python-docx) | Upload | 4 |
| Backend: Chunking strategy (recursive, 500 tokens) | Extraction | 3 |
| Backend: Embedding service (OpenAI/text-embedding-3-small) | Chunking | 4 |
| Backend: pgvector storage + HNSW index | Embeddings | 3 |
| Backend: Retriever (top-k cosine similarity) | Vector store | 4 |
| Backend: RAG service (retrieve → prompt → generate) | Retriever + LLM | 6 |
| Backend: Citation building from retrieved chunks | RAG | 3 |
| Frontend: Upload UI, document list, status polling | Upload API | 5 |
| Frontend: Citation display in messages | RAG citations | 3 |
| **Integration test: Upload PDF → Ask question → See citations** | Both | 3 |

### Sprint 5: Admin & Hardening (Week 5)
| Task | Dependencies | Est. Hours |
|------|--------------|------------|
| Backend: Admin endpoints (documents, stats) | Sprint 4 | 4 |
| Frontend: Admin documents page | Admin API | 4 |
| Backend: Rate limiting middleware | All APIs | 3 |
| Backend: Comprehensive error handling + logging | All | 3 |
| Backend: Unit tests (services, repos) | All backend | 6 |
| Frontend: Component tests (React Testing Library) | All frontend | 4 |
| E2E tests (Playwright): Auth, Chat, Upload, Admin | All | 6 |
| Documentation: README, env.example, API docs | All | 4 |

---

## 8. Testing & Acceptance Checklist

### 8.1 Unit Tests (Target: 80% coverage)
- [ ] Auth service: hash/verify, token create/validate, password policy
- [ ] Conversation service: CRUD, ownership checks, soft delete
- [ ] Document service: validation, status transitions
- [ ] Chunker: splits correctly, preserves metadata, handles edge cases
- [ ] Embedding service: batch processing, error handling
- [ ] Retriever: top-k, score threshold, filtering
- [ ] RAG service: prompt construction, citation mapping
- [ ] LLM adapters: interface compliance, streaming, error mapping

### 8.2 Integration Tests
- [ ] Auth flow: register → login → access protected → logout → blocked
- [ ] Conversation isolation: User A cannot read User B's conversations
- [ ] Document upload: valid PDF → processing → ready → searchable
- [ ] Document upload: invalid file (exe, >10MB) → rejected
- [ ] RAG: Question with relevant docs → answer + citations
- [ ] RAG: Question without relevant docs → "I don't know" response
- [ ] Admin: Non-admin blocked from admin endpoints

### 8.3 End-to-End Tests (Playwright)
- [ ] Happy path: Register → Login → New chat → Ask → See answer → New chat → History
- [ ] Upload flow: Drag PDF → Wait for ready → Ask about PDF → See citation
- [ ] Mobile: Viewport 375px → Sidebar drawer works → Chat usable
- [ ] Error: Disconnect network → Retry works → Message sends
- [ ] Admin: Login as admin → See all docs → Delete doc → Gone from user view

### 8.4 Security Tests
- [ ] SQL injection attempt in search → No error, no data leak
- [ ] XSS in message content → Rendered safely (no script execution)
- [ ] Path traversal in filename → Sanitized to UUID
- [ ] JWT tampering → Rejected (signature invalid)
- [ ] Expired token → 401, refresh works
- [ ] Rate limit exceeded → 429 with Retry-After header

---

## 9. Local Setup & Deployment Plan

### 9.1 Prerequisites
- Docker Desktop (≥ 4.0) or Docker Engine + Compose plugin
- Node.js 20+ (for frontend dev outside container)
- Python 3.11+ (for backend dev outside container)
- Git
- OpenAI API key (or compatible provider)

### 9.2 Environment Variables (`.env.example`)

```bash
# Application
APP_ENV=development
APP_HOST=0.0.0.0
APP_PORT=8000
FRONTEND_URL=http://localhost:5173

# Database
DATABASE_URL=postgresql+asyncpg://postgres:postgres@db:5432/campusgpt
POSTGRES_USER=postgres
POSTGRES_PASSWORD=postgres
POSTGRES_DB=campusgpt

# Security
SECRET_KEY=your-super-secret-key-min-32-chars-change-in-production
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=15
REFRESH_TOKEN_EXPIRE_DAYS=7
ARGON2_TIME_COST=3
ARGON2_MEMORY_COST=65536
ARGON2_PARALLELISM=4

# LLM Provider (choose one)
LLM_PROVIDER=openai  # openai | anthropic | local
OPENAI_API_KEY=sk-...
OPENAI_MODEL=gpt-4o-mini
OPENAI_EMBEDDING_MODEL=text-embedding-3-small
# ANTHROPIC_API_KEY=...
# LOCAL_LLM_BASE_URL=http://localhost:11434/v1

# File Storage
UPLOAD_DIR=/app/uploads
MAX_UPLOAD_SIZE_MB=10
ALLOWED_MIME_TYPES=application/pdf,text/plain,text/markdown

# Rate Limiting
RATE_LIMIT_AUTH_PER_MINUTE=5
RATE_LIMIT_CHAT_PER_MINUTE=30
RATE_LIMIT_UPLOAD_PER_HOUR=10

# Logging
LOG_LEVEL=INFO
LOG_FORMAT=json
```

### 9.3 Docker Compose (Development)

```yaml
# docker-compose.yml
version: '3.8'

services:
  db:
    image: pgvector/pgvector:pg16
    environment:
      POSTGRES_USER: ${POSTGRES_USER}
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD}
      POSTGRES_DB: ${POSTGRES_DB}
    volumes:
      - postgres_data:/var/lib/postgresql/data
    ports:
      - "5432:5432"
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U ${POSTGRES_USER}"]
      interval: 5s
      timeout: 5s
      retries: 5

  backend:
    build:
      context: ./backend
      dockerfile: Dockerfile.dev
    environment:
      - DATABASE_URL=postgresql+asyncpg://${POSTGRES_USER}:${POSTGRES_PASSWORD}@db:5432/${POSTGRES_DB}
      - FRONTEND_URL=http://localhost:5173
    env_file: .env
    volumes:
      - ./backend:/app
      - uploads:/app/uploads
    ports:
      - "8000:8000"
    depends_on:
      db:
        condition: service_healthy
    command: uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

  frontend:
    build:
      context: ./frontend
      dockerfile: Dockerfile.dev
    environment:
      - VITE_API_URL=http://localhost:8000
    volumes:
      - ./frontend:/app
      - /app/node_modules
    ports:
      - "5173:5173"
    depends_on:
      - backend

volumes:
  postgres_data:
  uploads:
```

### 9.4 Startup Commands

```bash
# 1. Clone and configure
git clone <repo>
cd campusgpt
cp .env.example .env
# Edit .env with your API keys

# 2. Start all services
docker compose up --build

# 3. Access
# Frontend: http://localhost:5173
# Backend API: http://localhost:8000
# API Docs: http://localhost:8000/docs

# 4. Run tests
docker compose exec backend pytest -v
docker compose exec frontend npm run test
docker compose exec frontend npm run test:e2e
```

### 9.5 Database Migrations
```bash
# Create migration
docker compose exec backend alembic revision --autogenerate -m "description"

# Apply migrations
docker compose exec backend alembic upgrade head

# Rollback
docker compose exec backend alembic downgrade -1
```

---

## 10. Key Decisions Explained (Beginner-Friendly)

### Why PostgreSQL + pgvector instead of a vector database?
**Simple answer**: One database to manage, backup, secure, and monitor. pgvector is mature, supports HNSW indexes for fast similarity search, and handles 100K+ vectors easily. You only need a dedicated vector DB (Pinecone, Weaviate) when you have millions of vectors or need multi-tenancy isolation at the infrastructure level.

### Why JWT in HttpOnly cookies instead of localStorage?
**Security**: localStorage is accessible to any JavaScript on your page (XSS vulnerability). HttpOnly cookies cannot be read by JavaScript. SameSite=Strict prevents CSRF. This is the modern best practice for SPAs.

### Why SSE instead of WebSockets for streaming?
**Simplicity**: SSE works over standard HTTP/2, reuses existing authentication (cookies), auto-reconnects, and doesn't need a separate WebSocket server or connection lifecycle management. For one-way streaming (server → client), it's the right tool.

### Why a provider-agnostic LLM interface?
**Flexibility**: Today you use OpenAI. Tomorrow you might switch to Anthropic, or self-host Llama 3 via Ollama, or use a college-provided model. An abstract interface (protocol/ABC) means you change one adapter class, not your entire application.

### Why modular monolith instead of microservices?
**Operational simplicity**: One deploy, one database, shared types, easy debugging, simple transactions. Microservices add network latency, distributed tracing complexity, eventual consistency bugs, and DevOps overhead. Split only when you have a proven scaling bottleneck or team boundary.

### Why Tailwind CSS?
**Speed + Consistency**: Utility-first means you build custom designs without writing CSS files. Design tokens (colors, spacing, radii) are in one config file. No context-switching between HTML and CSS. Purges unused styles automatically.

---

## 11. Next Steps

1. **Review this plan** — Ask questions, suggest changes
2. **Initialize repository** — Create folder structure, Docker files, configs
3. **Sprint 1** — Foundation: Docker, DB, Auth, Basic Frontend
4. **Iterate** — Each sprint ends with working, tested software

---

*Document Version: 1.0 | Created: Phase 1 Planning | Status: Ready for Review*