# CampusGPT — Institutional AI Assistant

![Python](https://img.shields.io/badge/Python-3.11+-blue?logo=python)
![FastAPI](https://img.shields.io/badge/FastAPI-0.110+-green?logo=fastapi)
![React](https://img.shields.io/badge/React-18+-blue?logo=react)
![TypeScript](https://img.shields.io/badge/TypeScript-5+-blue?logo=typescript)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-16-blue?logo=postgresql)
![pgvector](https://img.shields.io/badge/pgvector-enabled-blue)
![Docker](https://img.shields.io/badge/Docker-ready-blue?logo=docker)
![License](https://img.shields.io/badge/License-MIT-green)

A production-ready, **ChatGPT-like AI platform** for educational institutions. Built with **Retrieval-Augmented Generation (RAG)** for grounded, source-cited answers from institutional documents and websites.

---

## Project Vision

CampusGPT provides students, faculty, and administrators with a secure, intelligent interface to access:

- **Academic assistance** — Study help, concept explanations, assignment guidance
- **Institutional knowledge** — Policies, procedures, regulations, calendars
- **Research support** — Literature search, paper summarization, citation help
- **Document intelligence** — Upload, process, and query PDFs, docs, web pages
- **Verifiable answers** — Every response cites sources with page/chunk references

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              CAMPUSGPT ARCHITECTURE                          │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│   ┌──────────────┐     HTTPS/WSS      ┌──────────────────────────────────┐  │
│   │   FRONTEND   │ ◄──────────────────► │           BACKEND                │  │
│   │  (React 18 + │    REST + SSE       │  (FastAPI + Python 3.11)         │  │
│   │  TypeScript) │                    │                                    │  │
│   └──────────────┘                    └──────────────┬───────────────────┘  │
│                                                        │                     │
│              ┌────────────────────────────────────────┼──────────────────┐  │
│              ▼                                        ▼                  ▼  │
│       ┌─────────────────┐                    ┌─────────────────┐  ┌────────────┐
│       │   LLM PROVIDER  │                    │  EMBEDDING      │  │ POSTGRESQL │
│       │  (Ollama /      │                    │  SERVICE        │  │  16 +      │
│       │   OpenAI /      │                    │  (Ollama /      │  │ pgvector   │
│       │   Anthropic)    │                    │   OpenAI)       │  │ (Primary   │
│       └─────────────────┘                    └─────────────────┘  │   DB)      │
│                                                                     └────────────┘
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Data Flow

```
User Query ──► Embedding ──► Vector Search (pgvector) ──► Top-K Chunks ──► LLM ──► Cited Answer
                    │                │                        │
                    │                │                        └─► Source Citations
                    │                └─► HNSW Index (cosine similarity)
                    └─► nomic-embed-text (768-dim)
```

---

## Technology Stack

| Layer | Technology | Version |
|-------|------------|---------|
| **Frontend** | React, TypeScript, Vite, Tailwind CSS | 18 / 5 / 5 / 3 |
| **Backend** | FastAPI, SQLAlchemy 2.0, Pydantic v2 | 0.110 / 2.0 / 2 |
| **Database** | PostgreSQL + pgvector | 16 / 0.7+ |
| **Vector Search** | pgvector (HNSW index) | 0.7+ |
| **LLM Provider** | Ollama (local) / OpenAI / Anthropic | Latest |
| **Embeddings** | nomic-embed-text (768-dim) | Latest |
| **Auth** | JWT (HttpOnly cookies), Argon2id | - |
| **Containerization** | Docker, Docker Compose | Latest |
| **Testing** | pytest, Vitest, Playwright | Latest |

---

## Project Structure

```
campusgpt/
├── frontend/                          # React 18 + TypeScript + Vite
│   ├── src/
│   │   ├── components/                # Reusable UI components
│   │   ├── pages/                     # Route-level components
│   │   ├── features/                  # Feature-specific logic (auth, chat)
│   │   ├── hooks/                     # Custom React hooks
│   │   ├── services/                  # API clients
│   │   ├── types/                     # TypeScript interfaces
│   │   └── styles/                    # Global CSS, Tailwind
│   ├── package.json
│   ├── vite.config.ts
│   └── Dockerfile.dev
│
├── backend/                            # FastAPI + Python 3.11
│   ├── app/
│   │   ├── api/v1/                    # API route handlers
│   │   ├── core/                      # Config, security, database
│   │   ├── models/                    # SQLAlchemy ORM models
│   │   ├── schemas/                   # Pydantic request/response models
│   │   ├── services/                  # Business logic
│   │   ├── repositories/              # Data access layer
│   │   ├── ai/                        # LLM provider adapters
│   │   ├── ingestion/                 # Document ingestion & web scraping
│   │   └── rag/                       # RAG pipeline components
│   ├── scripts/                       # Ingestion & utility scripts
│   ├── requirements.txt
│   └── Dockerfile.dev
│
├── migrations/                         # Alembic database migrations
├── docker-compose.yml
├── .env.example
└── README.md
```

---

## Quick Start

### Prerequisites

- **Docker Desktop** ≥ 4.0 (or Docker Engine + Compose plugin)
- **Git**
- **Ollama** (for local LLM/embeddings) — *or* OpenAI/Anthropic API keys

---

### 1. Clone & Configure

```bash
git clone <repository-url>
cd campusgpt

# Copy environment template
cp .env.example .env

# Edit .env with your configuration
# Required: SECRET_KEY, LLM_PROVIDER (local/openai/anthropic)
```

### 2. Start Ollama (for local LLM/embeddings)

```bash
# Option A: Docker (recommended)
docker compose up -d ollama
docker exec campusgpt-ollama ollama pull nomic-embed-text
docker exec campusgpt-ollama ollama pull llama3.2:3b

# Option B: Host installation
# ollama pull nomic-embed-text
# ollama pull llama3.2:3b
```

### 3. Start All Services

```bash
# Development (with hot reload)
docker compose up -d --build

# View logs
docker compose logs -f backend
```

### 4. Access the Application

| Service | URL |
|---------|-----|
| **Frontend** | http://localhost:5173 |
| **Backend API** | http://localhost:8000 |
| **API Docs (Swagger)** | http://localhost:8000/docs |
| **Database** | localhost:5432 |

---

### 5. Load Institutional Data (MGIT Example)

```bash
# Load the already-scraped pages in backend/data/scraped/mgit (no website access).
# Keeps the newest copy of each page, strips site menus/sidebars, skips pages
# already loaded. Add --replace to re-ingest everything.
docker compose exec backend python scripts/load_scraped_mgit.py

# Or scrape the website again and ingest the result
docker compose exec backend python scripts/ingest_mgit.py
```

Website pages are **public**: every user's answers can use them.

---

### 6. Create Account & Start Chatting

1. Open http://localhost:5173 and click **Sign up**
2. Confirm your email. In development (`EMAIL_BACKEND=console`) the link is printed in the backend log:
   `docker compose logs backend | grep verify-email`
3. Sign in and start chatting

### 7. Make Yourself an Admin

```bash
docker compose exec backend python scripts/make_admin.py you@college.edu
```

Admins see every document, can delete any document, and can tick **Share with everyone**
when uploading to add a file to the campus knowledge base.

---

## Configuration

### Environment Variables (`.env`)

```bash
# ─── Application ──────────────────────────────────────────────
APP_ENV=development
APP_HOST=0.0.0.0
APP_PORT=8000
FRONTEND_URL=http://localhost:5173

# ─── Database ─────────────────────────────────────────────────
DATABASE_URL=postgresql+asyncpg://postgres:postgres@db:5432/campusgpt
POSTGRES_USER=postgres
POSTGRES_PASSWORD=postgres
POSTGRES_DB=campusgpt

# ─── Security (CHANGE IN PRODUCTION!) ────────────────────────
SECRET_KEY=your-super-secret-key-min-32-chars-change-in-production
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=15
REFRESH_TOKEN_EXPIRE_DAYS=7

# ─── LLM Provider (choose one) ───────────────────────────────
# Local (Ollama) — recommended for privacy & cost
LLM_PROVIDER=local
LOCAL_LLM_BASE_URL=http://ollama:11434
LOCAL_LLM_MODEL=llama3.2:3b
LOCAL_EMBEDDING_MODEL=nomic-embed-text

# OpenAI (cloud)
# LLM_PROVIDER=openai
# OPENAI_API_KEY=sk-xxx
# OPENAI_MODEL=gpt-4o-mini
# OPENAI_EMBEDDING_MODEL=text-embedding-3-small

# Anthropic (cloud)
# LLM_PROVIDER=anthropic
# ANTHROPIC_API_KEY=sk-ant-xxx
# ANTHROPIC_MODEL=claude-opus-5-5
# EMBEDDING_PROVIDER=local   # Anthropic has no embeddings API

# ─── File Storage ─────────────────────────────────────────────
UPLOAD_DIR=/app/uploads
MAX_UPLOAD_SIZE_MB=10
ALLOWED_MIME_TYPES=application/pdf,text/plain,text/markdown

# ─── RAG Configuration ────────────────────────────────────────
CHUNK_SIZE=500
CHUNK_OVERLAP=100
TOP_K_RETRIEVAL=5
# Model-dependent: ~0.5 suits nomic-embed-text, ~0.7 suits OpenAI embeddings
SIMILARITY_THRESHOLD=0.5
MAX_CONTEXT_CHUNKS=3

# ─── Web Scraping / Ingestion ────────────────────────────────
MGIT_BASE_URL=https://mgit.ac.in
MGIT_SCRAPE_DELAY_SECONDS=2
MGIT_MAX_PAGES=100
MGIT_ALLOWED_PATHS=/,/about,/admissions,/academics,/departments,/placements,/notices,/events
```

---

## Key Features

| Feature | Status | Description |
|---------|--------|-------------|
| **Authentication** | ✅ | JWT (HttpOnly cookies), Argon2id, rotating refresh tokens |
| **Email Verification** | ✅ | Signed 24h links; console output in dev, SMTP in production |
| **Rate Limiting** | ✅ | Sign-in per account and per IP, chat and uploads per IP (429 + Retry-After) |
| **Chat Interface** | ✅ | Conversation history, streaming (SSE), citations |
| **Document Upload** | ✅ | PDF, TXT, MD with automatic processing |
| **Document Privacy** | ✅ | Uploads are private to their owner; website pages and admin-shared files are public |
| **RAG Pipeline** | ✅ | pgvector similarity search, HNSW index |
| **Source Citations** | ✅ | Page/chunk references on every answer |
| **Web Scraping** | ✅ | MGIT scraper with robots.txt compliance |
| **Document Ingestion** | ✅ | Scrape → Chunk → Embed → Store pipeline |
| **Vector Search** | ✅ | pgvector HNSW index, cosine similarity |
| **Admin Dashboard** | ✅ | Document management, ingestion monitoring |
| **Migrations** | ✅ | Alembic owns the schema; applied automatically on container start |
| **Responsive UI** | ✅ | Mobile, tablet, desktop |

---

## API Documentation

Once running: **http://localhost:8000/docs** (Swagger UI)

### Key Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/v1/auth/register` | Register user (emails a confirmation link) |
| `POST` | `/api/v1/auth/verify-email` | Confirm email with the link's token |
| `POST` | `/api/v1/auth/resend-verification` | Send a new confirmation link |
| `POST` | `/api/v1/auth/login` | Login |
| `POST` | `/api/v1/auth/logout` | Logout |
| `GET` | `/api/v1/auth/me` | Current user |
| `GET` | `/api/v1/conversations` | List conversations |
| `POST` | `/api/v1/conversations` | Create conversation |
| `GET` | `/api/v1/conversations/{id}` | Get conversation + messages |
| `POST` | `/api/v1/conversations/{id}/messages` | Send message (SSE stream) |
| `POST` | `/api/v1/documents/upload` | Upload document (admins: `share_with_everyone`) |
| `POST` | `/api/v1/documents/{id}/reprocess` | Re-chunk and re-embed a document |
| `GET` | `/api/v1/documents` | List documents |
| `POST` | `/api/v1/documents/ingest/mgit` | Scrape and ingest MGIT (admin) |

---

## Testing

```bash
# Backend tests (use their own campusgpt_test database; dev data is never touched)
docker compose exec backend pytest -v
docker compose exec backend pytest --cov=app --cov-report=html

# Frontend unit tests
docker compose exec frontend npm run test

# Browser end-to-end tests against the running app. Needs one verified student
# account and one admin account; the frontend image includes Chromium.
docker compose exec   -e E2E_CHROMIUM_PATH=/usr/bin/chromium -e E2E_API_HOST=backend:8000   -e E2E_USER_EMAIL=student@college.edu -e E2E_USER_PASSWORD=...   -e E2E_ADMIN_EMAIL=admin@college.edu -e E2E_ADMIN_PASSWORD=...   frontend npm run test:e2e

# Linting
docker compose exec backend ruff check .
docker compose exec backend ruff format .
docker compose exec frontend npm run lint
```

---

## Database Management

The schema is managed by Alembic (`backend/migrations/versions`). The backend container runs
`scripts/migrate.py` before starting, which applies pending migrations. Databases created before
migrations existed are recognised and stamped at the baseline first.

```bash
# Create a migration after changing a model, then review the generated file
docker compose exec backend alembic revision --autogenerate -m "description"

# Apply migrations (also happens automatically on start)
docker compose exec backend python scripts/migrate.py

# Check the models and the database agree
docker compose exec backend alembic check

# Rollback
docker compose exec backend alembic downgrade -1

# Shell access
docker compose exec db psql -U postgres -d campusgpt
```

---

## Roadmap

### Phase 2: Knowledge Platform
- [ ] Modular document ingestion pipeline
- [ ] Advanced search & filtering
- [ ] Document versioning & updates

### Phase 3: Institutional AI
- [ ] RBAC with configurable roles
- [ ] Department-level data separation
- [ ] Personalized services integration

### Phase 4: Production Engineering
- [ ] Security audit
- [ ] AI quality evaluation
- [ ] Load testing & optimization
- [ ] CI/CD pipeline

---

## Contributing

```bash
# 1. Fork & clone
# 2. Create branch: git checkout -b feature/amazing-feature
# 3. Make changes + write tests
# 4. Run linting: ruff check . && npm run lint
# 5. Run tests: pytest && npm run test
# 6. Submit PR
```

---

## License

MIT License — see [LICENSE](LICENSE) for details.

---

## Acknowledgments

- [FastAPI](https://fastapi.tiangolo.com/) — Modern async web framework
- [pgvector](https://github.com/pgvector/pgvector) — Vector search in PostgreSQL
- [Ollama](https://ollama.com/) — Local LLM inference
- [Tailwind CSS](https://tailwindcss.com/) — Utility-first CSS
- [Lucide](https://lucide.dev/) — Beautiful icons

---

**Built with ❤️ for educational institutions worldwide.**