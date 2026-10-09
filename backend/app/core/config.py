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

    # Database Settings
    DATABASE_ENGINE: str = os.getenv("DATABASE_ENGINE", "postgres").strip().lower()
    PGHOST: str = os.getenv("PGHOST", "127.0.0.1").strip()
    PGPORT: int = int(os.getenv("PGPORT", "5432"))
    PGDATABASE: str = os.getenv("PGDATABASE", "sqlight").strip()
    PGUSER: str = os.getenv("PGUSER", "Thriveni").strip()
    PGPASSWORD: str = os.getenv("PGPASSWORD", "").strip()

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

    # Compression
    GZIP_MINIMUM_SIZE: int = 1000

    # Paths
    BASE_DIR: Path = BASE_DIR
    TEMP_CSV_DIR: Path = BASE_DIR / "temp_uploads"
    INVOICE_DIR: Path = BASE_DIR / "generated_invoices"


settings = Settings()
settings.TEMP_CSV_DIR.mkdir(parents=True, exist_ok=True)
settings.INVOICE_DIR.mkdir(parents=True, exist_ok=True)
