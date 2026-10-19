# ==============================================================================
# CampusGPT Backend — Configuration
# ==============================================================================
from functools import lru_cache
from typing import List, Optional
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # --------------------------------------------------------------------------
    # Application
    # --------------------------------------------------------------------------
    app_env: str = Field(default="development", alias="APP_ENV")
    app_host: str = Field(default="0.0.0.0", alias="APP_HOST")
    app_port: int = Field(default=8000, alias="APP_PORT")
    frontend_url: str = Field(default="http://localhost:5173", alias="FRONTEND_URL")

    # --------------------------------------------------------------------------
    # Database
    # --------------------------------------------------------------------------
    database_url: str = Field(alias="DATABASE_URL")
    postgres_user: str = Field(default="postgres", alias="POSTGRES_USER")
    postgres_password: str = Field(default="postgres", alias="POSTGRES_PASSWORD")
    postgres_db: str = Field(default="campusgpt", alias="POSTGRES_DB")

    # --------------------------------------------------------------------------
    # Security
    # --------------------------------------------------------------------------
    secret_key: str = Field(alias="SECRET_KEY")
    jwt_algorithm: str = Field(default="HS256", alias="JWT_ALGORITHM")
    access_token_expire_minutes: int = Field(default=15, alias="ACCESS_TOKEN_EXPIRE_MINUTES")
    refresh_token_expire_days: int = Field(default=7, alias="REFRESH_TOKEN_EXPIRE_DAYS")

    # Argon2id parameters
    argon2_time_cost: int = Field(default=3, alias="ARGON2_TIME_COST")
    argon2_memory_cost: int = Field(default=65536, alias="ARGON2_MEMORY_COST")
    argon2_parallelism: int = Field(default=4, alias="ARGON2_PARALLELISM")

    # --------------------------------------------------------------------------
    # LLM Provider
    # --------------------------------------------------------------------------
    llm_provider: str = Field(default="openai", alias="LLM_PROVIDER")

    # OpenAI
    openai_api_key: Optional[str] = Field(default=None, alias="OPENAI_API_KEY")
    openai_model: str = Field(default="gpt-4o-mini", alias="OPENAI_MODEL")
    openai_embedding_model: str = Field(default="text-embedding-3-small", alias="OPENAI_EMBEDDING_MODEL")
    openai_base_url: str = Field(default="https://api.openai.com/v1", alias="OPENAI_BASE_URL")

    # Anthropic
    anthropic_api_key: Optional[str] = Field(default=None, alias="ANTHROPIC_API_KEY")
    anthropic_model: str = Field(default="claude-opus-5-5", alias="ANTHROPIC_MODEL")
    anthropic_base_url: str = Field(default="https://api.anthropic.com/v1", alias="ANTHROPIC_BASE_URL")

    # Local
    local_llm_base_url: Optional[str] = Field(default=None, alias="LOCAL_LLM_BASE_URL")
    local_llm_model: Optional[str] = Field(default=None, alias="LOCAL_LLM_MODEL")
    local_embedding_model: Optional[str] = Field(default=None, alias="LOCAL_EMBEDDING_MODEL")

    # Embedding source when LLM_PROVIDER=anthropic (Anthropic has no embeddings API)
    embedding_provider: str = Field(default="local", alias="EMBEDDING_PROVIDER")

    # Must match the embedding model output (nomic-embed-text: 768, text-embedding-3-small: 1536)
    embedding_dimension: int = Field(default=768, alias="EMBEDDING_DIMENSION")

    # --------------------------------------------------------------------------
    # File Storage
    # --------------------------------------------------------------------------
    upload_dir: str = Field(default="/app/uploads", alias="UPLOAD_DIR")
    max_upload_size_mb: int = Field(default=10, alias="MAX_UPLOAD_SIZE_MB")
    allowed_mime_types: str = Field(default="application/pdf,text/plain,text/markdown", alias="ALLOWED_MIME_TYPES")

    @field_validator("allowed_mime_types")
    @classmethod
    def parse_mime_types(cls, v: str) -> List[str]:
        return [t.strip() for t in v.split(",")]

    # --------------------------------------------------------------------------
    # Email (verification links)
    # --------------------------------------------------------------------------
    require_email_verification: bool = Field(default=True, alias="REQUIRE_EMAIL_VERIFICATION")
    email_verification_expire_hours: int = Field(default=24, alias="EMAIL_VERIFICATION_EXPIRE_HOURS")
    # "console" prints emails to the backend log (development); "smtp" sends them
    email_backend: str = Field(default="console", alias="EMAIL_BACKEND")
    email_from: str = Field(default="CampusGPT <no-reply@campusgpt.local>", alias="EMAIL_FROM")
    smtp_host: Optional[str] = Field(default=None, alias="SMTP_HOST")
    smtp_port: int = Field(default=587, alias="SMTP_PORT")
    smtp_username: Optional[str] = Field(default=None, alias="SMTP_USERNAME")
    smtp_password: Optional[str] = Field(default=None, alias="SMTP_PASSWORD")
    smtp_use_tls: bool = Field(default=True, alias="SMTP_USE_TLS")

    # --------------------------------------------------------------------------
    # Rate Limiting
    # --------------------------------------------------------------------------
    rate_limit_enabled: bool = Field(default=True, alias="RATE_LIMIT_ENABLED")
    rate_limit_auth_per_minute: int = Field(default=5, alias="RATE_LIMIT_AUTH_PER_MINUTE")  # per account
    rate_limit_auth_per_ip_per_minute: int = Field(default=60, alias="RATE_LIMIT_AUTH_PER_IP_PER_MINUTE")
    rate_limit_chat_per_minute: int = Field(default=30, alias="RATE_LIMIT_CHAT_PER_MINUTE")
    rate_limit_upload_per_hour: int = Field(default=10, alias="RATE_LIMIT_UPLOAD_PER_HOUR")

    # --------------------------------------------------------------------------
    # Logging
    # --------------------------------------------------------------------------
    log_level: str = Field(default="INFO", alias="LOG_LEVEL")
    log_format: str = Field(default="json", alias="LOG_FORMAT")

    # --------------------------------------------------------------------------
    # RAG Configuration
    # --------------------------------------------------------------------------
    chunk_size: int = Field(default=500, alias="CHUNK_SIZE")
    chunk_overlap: int = Field(default=100, alias="CHUNK_OVERLAP")
    top_k_retrieval: int = Field(default=5, alias="TOP_K_RETRIEVAL")
    similarity_threshold: float = Field(default=0.5, alias="SIMILARITY_THRESHOLD")
    max_context_chunks: int = Field(default=3, alias="MAX_CONTEXT_CHUNKS")

    # --------------------------------------------------------------------------
    # Web Scraping / Ingestion
    # --------------------------------------------------------------------------
    mgit_base_url: str = Field(default="https://mgit.ac.in", alias="MGIT_BASE_URL")
    mgit_scrape_delay_seconds: float = Field(default=2.0, alias="MGIT_SCRAPE_DELAY_SECONDS")
    mgit_max_pages: int = Field(default=100, alias="MGIT_MAX_PAGES")
    mgit_allowed_paths: str = Field(default="/,/about,/admissions,/academics,/departments,/placements,/notices,/events,/accreditation,/controller-of-examinations,/library,/transport,/recruitment,/contact-us,/campus-life,/mandatory-disclosures,/aes-objectives", alias="MGIT_ALLOWED_PATHS")

    scraper_user_agent: str = Field(default="CampusGPT-Ingestion-Bot/1.0", alias="SCRAPER_USER_AGENT")
    scraper_respect_robots_txt: bool = Field(default=True, alias="SCRAPER_RESPECT_ROBOTS_TXT")
    scraper_max_concurrent: int = Field(default=3, alias="SCRAPER_MAX_CONCURRENT")

    # --------------------------------------------------------------------------
    # Computed Properties
    # --------------------------------------------------------------------------
    @property
    def is_development(self) -> bool:
        return self.app_env.lower() == "development"

    @property
    def is_production(self) -> bool:
        return self.app_env.lower() == "production"


@lru_cache
def get_settings() -> Settings:
    """Cached settings instance for dependency injection."""
    return Settings()


settings = get_settings()