from __future__ import annotations
import os
from pathlib import Path
from typing import Any
from urllib.parse import quote_plus
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker
from ..core.config import settings

def get_database_url() -> str:
    # 1. Direct DATABASE_URL environment variable (Render PostgreSQL injection)
    raw_url = os.environ.get("DATABASE_URL", "").strip()
    if raw_url:
        if raw_url.startswith("postgres://"):
            return raw_url.replace("postgres://", "postgresql+psycopg://", 1)
        elif raw_url.startswith("postgresql://") and "+psycopg" not in raw_url:
            return raw_url.replace("postgresql://", "postgresql+psycopg://", 1)
        return raw_url

    # 2. SQLite or Cloud fallback (Render / Vercel without remote PG)
    if settings.DATABASE_ENGINE in ("sqlite", "sqlite3") or (
        (os.environ.get("VERCEL") or os.environ.get("RENDER"))
        and (not os.environ.get("PGHOST") or os.environ.get("PGHOST") in ("localhost", "127.0.0.1"))
    ):
        import tempfile
        if os.environ.get("VERCEL") or os.environ.get("RENDER"):
            db_path = Path(tempfile.gettempdir()) / "ecommerce.db"
        else:
            db_path = settings.BASE_DIR / "ecommerce.db"
        try:
            db_path.parent.mkdir(parents=True, exist_ok=True)
        except Exception:
            pass
        return f"sqlite:///{db_path}"
    
    user = settings.PGUSER
    password = settings.PGPASSWORD
    host = settings.PGHOST
    port = settings.PGPORT
    dbname = settings.PGDATABASE
    
    if password:
        quoted_password = quote_plus(password)
        return f"postgresql+psycopg://{user}:{quoted_password}@{host}:{port}/{dbname}"
    return f"postgresql+psycopg://{user}@{host}:{port}/{dbname}"

DATABASE_URL = get_database_url()

connect_args = {}
if DATABASE_URL.startswith("sqlite"):
    connect_args = {"check_same_thread": False}
    engine = create_engine(
        DATABASE_URL,
        connect_args=connect_args,
        pool_pre_ping=settings.DB_POOL_PRE_PING,
        echo=False,
    )
else:
    engine = create_engine(
        DATABASE_URL,
        connect_args=connect_args,
        pool_size=settings.DB_POOL_SIZE,
        max_overflow=settings.DB_MAX_OVERFLOW,
        pool_timeout=settings.DB_POOL_TIMEOUT,
        pool_recycle=settings.DB_POOL_RECYCLE,
        pool_pre_ping=settings.DB_POOL_PRE_PING,
        echo=False,
    )

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db_pool_status() -> dict[str, Any]:
    """Inspect and return current database connection pool metrics."""
    pool = engine.pool
    is_sqlite = DATABASE_URL.startswith("sqlite")
    status = {
        "engine": "sqlite" if is_sqlite else "postgres",
        "pool_type": pool.__class__.__name__,
        "pool_pre_ping": settings.DB_POOL_PRE_PING,
    }
    if not is_sqlite:
        try:
            status.update({
                "pool_size": getattr(pool, "size", lambda: settings.DB_POOL_SIZE)(),
                "checked_in": getattr(pool, "checkedin", lambda: 0)(),
                "checked_out": getattr(pool, "checkedout", lambda: 0)(),
                "overflow": getattr(pool, "overflow", lambda: 0)(),
                "max_overflow": settings.DB_MAX_OVERFLOW,
                "pool_timeout": settings.DB_POOL_TIMEOUT,
                "pool_recycle": settings.DB_POOL_RECYCLE,
            })
        except Exception:
            pass
    return status


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

