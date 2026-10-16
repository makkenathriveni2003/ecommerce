import os
from pathlib import Path
from typing import List
from dotenv import load_dotenv

# Locate .env from backend folder or root
BASE_DIR = Path(__file__).resolve().parent.parent.parent
ENV_PATH = BASE_DIR / ".env"
load_dotenv(ENV_PATH)


class Settings:
    PROJECT_NAME: str = "ShopZone E-Commerce API"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api"
    ENVIRONMENT: str = os.getenv("ENVIRONMENT", "development").strip().lower()
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO").strip().upper()
    SENTRY_DSN: str = os.getenv("SENTRY_DSN", "").strip()
    PROMETHEUS_METRICS_ENABLED: bool = os.getenv("PROMETHEUS_METRICS_ENABLED", "true").lower() in ("true", "1", "yes")

    # Database Settings
    DATABASE_ENGINE: str = os.getenv("DATABASE_ENGINE", "postgres").strip().lower()
    PGHOST: str = os.getenv("PGHOST", "127.0.0.1").strip()
    PGPORT: int = int(os.getenv("PGPORT", "5432"))
    PGDATABASE: str = os.getenv("PGDATABASE", "sqlight").strip()
    PGUSER: str = os.getenv("PGUSER", "Thriveni").strip()
    PGPASSWORD: str = os.getenv("PGPASSWORD", "").strip()

    # Database Connection Pooling Settings (Day 25 Capstone)
    DB_POOL_SIZE: int = int(os.getenv("DB_POOL_SIZE", "20"))
    DB_MAX_OVERFLOW: int = int(os.getenv("DB_MAX_OVERFLOW", "30"))
    DB_POOL_TIMEOUT: int = int(os.getenv("DB_POOL_TIMEOUT", "30"))
    DB_POOL_RECYCLE: int = int(os.getenv("DB_POOL_RECYCLE", "1800"))
    DB_POOL_PRE_PING: bool = os.getenv("DB_POOL_PRE_PING", "true").lower() in ("true", "1", "yes")

    # JWT Authentication
    JWT_SECRET_KEY: str = os.getenv(
        "JWT_SECRET_KEY", "fZr7Wf-hO_iq7j3rM0ripJd0fidB7OoxeXV3Ur_OJQcqArNurmt_GLIEKpN7EB4o"
    ).strip()
    JWT_ALGORITHM: str = os.getenv("JWT_ALGORITHM", "HS256").strip()
    ACCESS_TOKEN_EXPIRE_MINUTES: int = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "1440"))

    # CORS
    FRONTEND_ORIGINS_RAW: str = os.getenv(
        "FRONTEND_ORIGINS",
        "http://localhost:5173,http://127.0.0.1:5173,http://localhost:5174,http://127.0.0.1:5174,http://localhost:4173,http://127.0.0.1:4173,http://localhost:3000,http://127.0.0.1:3000",
    )

    @property
    def cors_origins(self) -> list[str]:
        return [
            origin.strip()
            for origin in self.FRONTEND_ORIGINS_RAW.split(",")
            if origin.strip()
        ]

    # Celery & Redis
    CELERY_BROKER_URL: str = os.getenv(
        "CELERY_BROKER_URL", "redis://127.0.0.1:6379/0"
    ).strip()
    CELERY_RESULT_BACKEND: str = os.getenv(
        "CELERY_RESULT_BACKEND", "redis://127.0.0.1:6379/0"
    ).strip()

    # Rate Limiting (SlowAPI)
    RATE_LIMIT_ENABLED: bool = os.getenv("RATE_LIMIT_ENABLED", "true").lower() in ("true", "1", "yes")
    LOGIN_RATE_LIMIT: str = os.getenv("LOGIN_RATE_LIMIT", "5/minute")
    REGISTER_RATE_LIMIT: str = os.getenv("REGISTER_RATE_LIMIT", "5/minute")
    ORDER_RATE_LIMIT: str = os.getenv("ORDER_RATE_LIMIT", "20/minute")
    TASK_RATE_LIMIT: str = os.getenv("TASK_RATE_LIMIT", "30/minute")
    DEFAULT_RATE_LIMIT: str = os.getenv("DEFAULT_RATE_LIMIT", "100/minute")
    AI_RATE_LIMIT: str = os.getenv("AI_RATE_LIMIT", "20/minute")

    # AI Focus Settings (Groq, Gemini, Mistral, OpenAI-compatible)
    AI_PRIMARY_PROVIDER: str = os.getenv("AI_PRIMARY_PROVIDER", "gemini").strip().lower()
    AI_FALLBACK_PROVIDERS_RAW: str = os.getenv("AI_FALLBACK_PROVIDERS", "groq,mistral,openai_compatible").strip()

    @property
    def fallback_providers(self) -> list[str]:
        return [
            p.strip().lower()
            for p in self.AI_FALLBACK_PROVIDERS_RAW.split(",")
            if p.strip()
        ]

    # Groq API
    GROQ_API_KEY: str = os.getenv("GROQ_API_KEY", "").strip()
    GROQ_MODEL: str = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile").strip()
    GROQ_BASE_URL: str = os.getenv("GROQ_BASE_URL", "https://api.groq.com/openai/v1").strip()

    # Google Gemini API
    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "").strip()
    GEMINI_MODEL: str = os.getenv("GEMINI_MODEL", "gemini-1.5-flash").strip()

    # Mistral API
    MISTRAL_API_KEY: str = os.getenv("MISTRAL_API_KEY", "").strip()
    MISTRAL_MODEL: str = os.getenv("MISTRAL_MODEL", "mistral-small-latest").strip()
    MISTRAL_BASE_URL: str = os.getenv("MISTRAL_BASE_URL", "https://api.mistral.ai/v1").strip()

    # OpenAI-Compatible Endpoints
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "").strip()
    OPENAI_MODEL: str = os.getenv("OPENAI_MODEL", "gpt-4o-mini").strip()
    OPENAI_BASE_URL: str = os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1").strip()

    # AI Execution Parameters
    AI_REQUEST_TIMEOUT: float = float(os.getenv("AI_REQUEST_TIMEOUT", "30.0"))
    AI_MAX_RETRIES: int = int(os.getenv("AI_MAX_RETRIES", "2"))
    AI_RETRY_BACKOFF_FACTOR: float = float(os.getenv("AI_RETRY_BACKOFF_FACTOR", "0.5"))
    AI_MAX_MESSAGE_LENGTH: int = int(os.getenv("AI_MAX_MESSAGE_LENGTH", "1000"))
    AI_MAX_HISTORY_MESSAGES: int = int(os.getenv("AI_MAX_HISTORY_MESSAGES", "6"))

    # RAG & ChromaDB Persistence
    CHROMA_PERSIST_DIR: Path = BASE_DIR / os.getenv("CHROMA_PERSIST_DIR", "chroma_db").strip()
    EMBEDDING_PROVIDER: str = os.getenv("EMBEDDING_PROVIDER", "local_hash").strip().lower()
    EMBEDDING_MODEL: str = os.getenv("EMBEDDING_MODEL", "text-embedding-004").strip()
    RAG_TOP_K: int = int(os.getenv("RAG_TOP_K", "4"))
    RAG_CHUNK_SIZE: int = int(os.getenv("RAG_CHUNK_SIZE", "500"))
    RAG_CHUNK_OVERLAP: int = int(os.getenv("RAG_CHUNK_OVERLAP", "50"))

    # Compression
    GZIP_MINIMUM_SIZE: int = 1000

    # Paths
    BASE_DIR: Path = BASE_DIR
    TEMP_CSV_DIR: Path = BASE_DIR / "temp_uploads"
    INVOICE_DIR: Path = BASE_DIR / "generated_invoices"


settings = Settings()
settings.TEMP_CSV_DIR.mkdir(parents=True, exist_ok=True)
settings.INVOICE_DIR.mkdir(parents=True, exist_ok=True)
settings.CHROMA_PERSIST_DIR.mkdir(parents=True, exist_ok=True)
