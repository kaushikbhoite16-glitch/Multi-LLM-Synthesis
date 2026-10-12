import os
from typing import List
from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


def _normalize_database_url(url: str) -> str:
    """
    Normalize the DATABASE_URL to use the correct SQLAlchemy async driver.

    Render's managed PostgreSQL service provides the connection URL as
    'postgres://...' or 'postgresql://...'. SQLAlchemy's create_async_engine
    with a bare 'postgresql://' scheme selects psycopg (psycopg3) as the
    default async dialect. Since only asyncpg is installed, this causes
    ModuleNotFoundError: No module named 'psycopg'.

    This function rewrites any bare PostgreSQL scheme to 'postgresql+asyncpg://'
    so that the installed asyncpg driver is always selected for PostgreSQL
    connections. SQLite URLs are left unchanged.
    """
    if not url:
        return url
    if url.startswith("postgres://"):
        return url.replace("postgres://", "postgresql+asyncpg://", 1)
    if url.startswith("postgresql://"):
        return url.replace("postgresql://", "postgresql+asyncpg://", 1)
    # Already has a driver specifier (e.g. postgresql+asyncpg://, sqlite+aiosqlite://)
    return url


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="allow")

    PROJECT_NAME: str = "Multi-LLM Response Evaluation and Adaptive Answer Synthesis"
    API_V1_STR: str = "/api"

    # LLM Gateway
    OPENROUTER_API_KEY: str = os.getenv("OPENROUTER_API_KEY", "")
    OPENROUTER_BASE_URL: str = "https://openrouter.ai/api/v1"

    # Database
    # Default to local SQLite. When DATABASE_URL is set in environment (e.g. on Render),
    # the field_validator normalizes postgres:// or postgresql:// to postgresql+asyncpg://
    DATABASE_URL: str = "sqlite+aiosqlite:///./multi_llm.db"

    @field_validator("DATABASE_URL", mode="after")
    @classmethod
    def validate_database_url(cls, v: str) -> str:
        return _normalize_database_url(v)
    
    # Defaults
    DEFAULT_EVALUATOR_MODEL: str = os.getenv("DEFAULT_EVALUATOR_MODEL", "openai/gpt-4o-mini")
    DEFAULT_SYNTHESIS_MODEL: str = os.getenv("DEFAULT_SYNTHESIS_MODEL", "openai/gpt-4o-mini")
    DEFAULT_CANDIDATE_MODELS: List[str] = [
        "google/gemini-2.5-flash",
        "openai/gpt-4o-mini",
        "meta-llama/llama-3.1-8b-instruct"
    ]
    
    # Resource Limits
    MAX_COST_PER_QUERY: float = float(os.getenv("MAX_COST_PER_QUERY", "0.50"))
    MAX_TOKENS_PER_QUERY: int = int(os.getenv("MAX_TOKENS_PER_QUERY", "16000"))
    REQUEST_TIMEOUT_SECONDS: float = 60.0
    
    # Environment
    ENVIRONMENT: str = os.getenv("ENVIRONMENT", "development")
    MOCK_MODE: bool = os.getenv("MOCK_MODE", "false").lower() in ("true", "1", "yes")

    # Authentication & Security
    # IMPORTANT: JWT_SECRET_KEY MUST be set as a secret environment variable in
    # production (Render → Environment Variables). The default below is a dev-only
    # fallback — tokens signed with it are easily forged by anyone who can read
    # this repository. Any production deployment without this env var set is insecure.
    JWT_SECRET_KEY: str = os.getenv("JWT_SECRET_KEY", "dev-only-insecure-key-CHANGE-IN-PRODUCTION")
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7  # 7 days

    # Google OAuth
    GOOGLE_CLIENT_ID: str = os.getenv("GOOGLE_CLIENT_ID", "")
    GOOGLE_CLIENT_SECRET: str = os.getenv("GOOGLE_CLIENT_SECRET", "")

    # Administrator Initial Account
    # Set ADMIN_EMAIL and ADMIN_PASSWORD as environment variables in production.
    # The defaults below are acceptable fallbacks for local development only.
    ADMIN_EMAIL: str = os.getenv("ADMIN_EMAIL", "admin@multilllm.ai")
    ADMIN_PASSWORD: str = os.getenv("ADMIN_PASSWORD", "Admin@SecurePass2025!")

    # Email Delivery Configuration (Resend HTTPS API / SMTP compatibility)
    RESEND_API_KEY: str = os.getenv("RESEND_API_KEY", "")
    SMTP_HOST: str = os.getenv("SMTP_HOST", "")
    SMTP_PORT: int = int(os.getenv("SMTP_PORT", "587"))
    SMTP_USER: str = os.getenv("SMTP_USER", "")
    SMTP_PASSWORD: str = os.getenv("SMTP_PASSWORD", "")
    SMTP_FROM_EMAIL: str = os.getenv("SMTP_FROM_EMAIL", "")
    SMTP_TLS: bool = os.getenv("SMTP_TLS", "true").lower() in ("true", "1", "yes")

    @property
    def effective_resend_api_key(self) -> str:
        """Returns RESEND_API_KEY if provided, falling back to SMTP_PASSWORD for backward compatibility."""
        return (self.RESEND_API_KEY or self.SMTP_PASSWORD or "").strip()

    # Application Frontend URL (used for password reset links)
    FRONTEND_URL: str = os.getenv("FRONTEND_URL", "https://multi-llm-synthesis-web.vercel.app")

    # Testing flag: allows test suite to inspect reset tokens without mock bypasses
    TESTING: bool = os.getenv("TESTING", "false").lower() in ("true", "1", "yes")

settings = Settings()

