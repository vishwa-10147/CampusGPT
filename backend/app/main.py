# ==============================================================================
# CampusGPT Backend — Main Application
# ==============================================================================
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware

from app.core.config import settings
from app.core.database import init_db, close_db
from app.api.v1 import auth, conversations, messages, documents, admin
from app.api.deps import get_current_user


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    # Startup
    await init_db()
    yield
    # Shutdown
    await close_db()


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    app = FastAPI(
        title="CampusGPT API",
        description="Institutional AI Assistant API",
        version="0.1.0",
        docs_url="/docs" if settings.is_development else None,
        redoc_url="/redoc" if settings.is_development else None,
        lifespan=lifespan,
    )

    # Security middleware
    app.add_middleware(
        TrustedHostMiddleware,
        allowed_hosts=["*"] if settings.is_development else ["localhost", "127.0.0.1"],
    )

    # CORS middleware (browsers reject "*" for credentialed requests, so always name the origin)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[settings.frontend_url],
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
        allow_headers=["*"],
    )

    # Health check endpoint
    @app.get("/health", tags=["Health"])
    async def health_check():
        return {"status": "healthy", "version": "0.1.0"}

    # API routes
    app.include_router(auth.router, prefix="/api/v1")
    app.include_router(conversations.router, prefix="/api/v1")
    app.include_router(messages.router, prefix="/api/v1")
    app.include_router(documents.router, prefix="/api/v1")
    app.include_router(admin.router, prefix="/api/v1")

    # Root endpoint
    @app.get("/", tags=["Root"])
    async def root():
        return {
            "name": "CampusGPT API",
            "version": "0.1.0",
            "docs": "/docs",
            "health": "/health",
        }

    return app


app = create_app()