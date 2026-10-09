from __future__ import annotations
from pathlib import Path
from urllib.parse import quote_plus
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker
from ..core.config import settings

def get_database_url() -> str:
    if settings.DATABASE_ENGINE in ("sqlite", "sqlite3"):
        db_path = settings.BASE_DIR / "ecommerce.db"
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
    pool_pre_ping=True,
    echo=False,
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
