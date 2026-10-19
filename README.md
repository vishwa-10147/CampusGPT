# CampusGPT — Institutional AI Assistant

A professional, ChatGPT-like AI platform for colleges and educational institutions. Built with Retrieval-Augmented Generation (RAG) for grounded answers from institutional documents.

## 🎯 Project Vision

CampusGPT provides students, faculty, and administrators with a secure, intelligent interface to access:
- Academic assistance and study help
- College policies and procedures
- Research resources and institutional knowledge
- Document upload and querying capabilities
- Source-cited responses for verification

## 🏗️ Architecture Overview

```
┌─────────────┐     HTTPS/WSS      ┌─────────────┐
│  FRONTEND   │ ◄─────────────────► │  BACKEND    │
│  (React +   │    REST + SSE       │  (FastAPI)  │
│  TypeScript)│                    │             │
└─────────────┘                    └──────┬──────┘
                                           │
                    ┌──────────────────────┼──────────────────────┐
                    ▼                      ▼                      ▼
           ┌─────────────────┐    ┌─────────────────┐    ┌─────────────┐
           │  LLM PROVIDER   │    │  EMBEDDING      │    │  POSTGRESQL │
           │  (OpenAI/       │    │  SERVICE        │    │  + pgvector │
           │   Local)        │    │  (OpenAI/       │    │  (Primary   │
           └─────────────────┘    │   Local)        │    │   DB)       │
                                  └─────────────────┘    └─────────────┘
```

## 🛠️ Technology Stack

| Layer | Technology |
|-------|------------|
| **Frontend** | React 18, TypeScript, Vite, Tailwind CSS |
| **Backend** | Python 3.11, FastAPI, SQLAlchemy 2.0, Pydantic v2 |
| **Database** | PostgreSQL 16 + pgvector |
| **AI/ML** | Provider-agnostic (OpenAI, Anthropic, Local/Ollama) |
| **Auth** | JWT in HttpOnly cookies, Argon2id password hashing |
| **Infrastructure** | Docker, Docker Compose |
| **Testing** | pytest, Vitest, Playwright |

## 📁 Project Structure

```
campusgpt/
├── frontend/                 # React + TypeScript + Vite
│   ├── src/
│   │   ├── components/       # Reusable UI components
│   │   ├── pages/           # Route-level components
│   │   ├── features/        # Feature-specific logic (auth, chat)
│   │   ├── hooks/           # Custom React hooks
│   │   ├── services/        # API clients
│   │   ├── types/           # TypeScript interfaces
│   │   └── styles/          # Global CSS, Tailwind
│   ├── package.json
│   ├── vite.config.ts
│   └── Dockerfile.dev
├── backend/                  # FastAPI + Python
│   ├── app/
│   │   ├── api/v1/          # API route handlers
│   │   ├── core/            # Config, security, database
│   │   ├── models/          # SQLAlchemy ORM models
│   │   ├── schemas/         # Pydantic request/response models
│   │   ├── services/        # Business logic
│   │   ├── repositories/    # Data access layer
│   │   ├── ai/              # LLM provider adapters
│   │   └── rag/             # RAG pipeline components
│   ├── requirements.txt
│   └── Dockerfile.dev
├── migrations/               # Alembic database migrations
├── docker-compose.yml
├── .env.example
└── README.md
```

## 🚀 Quick Start

### Prerequisites

- Docker Desktop (≥ 4.0) or Docker Engine + Compose plugin
- Git
- OpenAI API key (or compatible provider)

### 1. Clone and Configure

```bash
git clone <repository-url>
cd campusgpt

# Copy environment template
cp .env.example .env

# Edit .env with your API keys
# Required: OPENAI_API_KEY, SECRET_KEY
```

### 2. Start Development Environment

```bash
# Start all services (database, backend, frontend)
docker compose up --build

# Or run in background
docker compose up -d --build
```

### 3. Access the Application

| Service | URL |
|---------|-----|
| Frontend | http://localhost:5173 |
| Backend API | http://localhost:8000 |
| API Documentation | http://localhost:8000/docs |
| Database | localhost:5432 |

### 4. Create Your First Account

1. Open http://localhost:5173
2. Click "Sign up" and create an account
3. Start chatting with CampusGPT!

## ⚙️ Configuration

### Environment Variables

All configuration is done via environment variables. Copy `.env.example` to `.env` and customize:

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

# Security (CHANGE IN PRODUCTION!)
SECRET_KEY=your-super-secret-key-min-32-chars-change-in-production
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=15
REFRESH_TOKEN_EXPIRE_DAYS=7

# LLM Provider (choose one)
LLM_PROVIDER=openai
OPENAI_API_KEY=sk-your-key-here
OPENAI_MODEL=gpt-4o-mini
OPENAI_EMBEDDING_MODEL=text-embedding-3-small

# File Storage
UPLOAD_DIR=/app/uploads
MAX_UPLOAD_SIZE_MB=10
ALLOWED_MIME_TYPES=application/pdf,text/plain,text/markdown

# RAG Configuration
CHUNK_SIZE=500
CHUNK_OVERLAP=50
TOP_K_RETRIEVAL=5
SIMILARITY_THRESHOLD=0.7
MAX_CONTEXT_CHUNKS=3
```

### Using Local LLMs (Ollama)

```bash
# In .env
LLM_PROVIDER=local
LOCAL_LLM_BASE_URL=http://host.docker.internal:11434/v1
LOCAL_LLM_MODEL=llama3.1:8b
LOCAL_EMBEDDING_MODEL=nomic-embed-text
```

Make sure Ollama is running on your host machine with the models pulled:
```bash
ollama pull llama3.1:8b
ollama pull nomic-embed-text
```

## 🧪 Testing

### Backend Tests

```bash
# Run all tests
docker compose exec backend pytest -v

# Run with coverage
docker compose exec backend pytest --cov=app --cov-report=html

# Run specific test file
docker compose exec backend pytest app/tests/test_auth.py -v
```

### Frontend Tests

```bash
# Unit tests
docker compose exec frontend npm run test

# E2E tests
docker compose exec frontend npm run test:e2e
```

## 📊 Database Management

### Create Migration

```bash
docker compose exec backend alembic revision --autogenerate -m "description"
```

### Apply Migrations

```bash
docker compose exec backend alembic upgrade head
```

### Rollback Migration

```bash
docker compose exec backend alembic downgrade -1
```

## 🔐 Security Features

- **Password Hashing**: Argon2id (memory-hard, GPU-resistant)
- **Authentication**: JWT access tokens (15min) + refresh tokens (7 days) in HttpOnly cookies
- **Authorization**: Server-side ownership checks on all resources
- **Rate Limiting**: Per-endpoint limits (auth: 5/min, chat: 30/min, upload: 10/hr)
- **CORS**: Configured for frontend origin only
- **Security Headers**: CSP, HSTS, X-Frame-Options, etc.
- **Input Validation**: Pydantic models with strict validation
- **File Upload Safety**: MIME type validation, size limits, secure filename generation

## 📝 API Documentation

Once running, visit http://localhost:8000/docs for interactive Swagger UI.

### Key Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/auth/register` | Register new user |
| POST | `/api/v1/auth/login` | Login |
| POST | `/api/v1/auth/logout` | Logout |
| GET | `/api/v1/auth/me` | Get current user |
| GET | `/api/v1/conversations` | List conversations |
| POST | `/api/v1/conversations` | Create conversation |
| GET | `/api/v1/conversations/{id}` | Get conversation with messages |
| POST | `/api/v1/conversations/{id}/messages` | Send message (streaming) |
| POST | `/api/v1/documents/upload` | Upload document |
| GET | `/api/v1/documents` | List documents |

## 🏭 Production Deployment

### 1. Build Production Images

```bash
# Frontend
docker build -t campusgpt-frontend:latest -f frontend/Dockerfile.prod ./frontend

# Backend
docker build -t campusgpt-backend:latest -f backend/Dockerfile.prod ./backend
```

### 2. Use Production Docker Compose

```bash
# Create production docker-compose.yml with:
# - Proper secrets management
# - Reverse proxy (nginx/traefik)
# - SSL termination
# - Resource limits
# - Health checks
# - Logging drivers
```

### 3. Required Production Changes

- [ ] Set `APP_ENV=production`
- [ ] Generate strong `SECRET_KEY` (32+ chars)
- [ ] Use PostgreSQL with proper credentials
- [ ] Configure HTTPS/TLS
- [ ] Set up proper logging aggregation
- [ ] Configure backup strategy for database
- [ ] Set up monitoring (Prometheus/Grafana)
- [ ] Configure rate limiting with Redis
- [ ] Use secrets manager for API keys

## 📦 Development Workflow

### Adding a New Feature

1. **Backend First**: Add models → repositories → services → schemas → API routes
2. **Database**: Create migration with `alembic revision --autogenerate`
3. **Frontend**: Add types → API client → components → pages → routing
4. **Test**: Write unit + integration tests
5. **Document**: Update README and API docs

### Code Style

```bash
# Backend
docker compose exec backend ruff check .
docker compose exec backend ruff format .
docker compose exec backend mypy app

# Frontend
docker compose exec frontend npm run lint
docker compose exec frontend npx tsc --noEmit
```

## 📚 Phase 1 MVP Features

- ✅ User registration and authentication (JWT + HttpOnly cookies)
- ✅ Chat interface with conversation history
- ✅ Streaming AI responses (SSE)
- ✅ Document upload (PDF, TXT, MD) with processing
- ✅ RAG with pgvector similarity search
- ✅ Source citations with page/chunk references
- ✅ Responsive UI (mobile, tablet, desktop)
- ✅ Admin interface for document management
- ✅ PostgreSQL + pgvector persistence
- ✅ Docker Compose development environment
- ✅ Automated tests (unit + integration)

## 🗺️ Roadmap

### Phase 2: College Knowledge Platform
- [ ] Modular document ingestion pipeline
- [ ] Alumni directory importer (with privacy compliance)
- [ ] Advanced search and filtering
- [ ] Document versioning and updates

### Phase 3: Role-Based Institutional AI
- [ ] RBAC with configurable roles
- [ ] Department-level data separation
- [ ] Personalized college services integration

### Phase 4: Production Engineering
- [ ] Comprehensive security audit
- [ ] AI quality evaluation suite
- [ ] Load testing and optimization
- [ ] CI/CD pipeline with staging
- [ ] Complete operational documentation

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/amazing-feature`
3. Make your changes with tests
4. Run linting and tests
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- [FastAPI](https://fastapi.tiangolo.com/) for the excellent async framework
- [pgvector](https://github.com/pgvector/pgvector) for vector similarity search in PostgreSQL
- [Tailwind CSS](https://tailwindcss.com/) for the utility-first CSS framework
- [Lucide](https://lucide.dev/) for beautiful icons
- [OpenAI](https://openai.com/) for LLM and embedding APIs

---

**Built with ❤️ for educational institutions worldwide.**