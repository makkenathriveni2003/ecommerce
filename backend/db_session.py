"""
Backward-compatibility adapter for db_session module.
Re-exports from app.db.session.
"""
from app.db.session import (
    engine,
    SessionLocal,
    Base,
    get_db,
    get_database_url,
    DATABASE_URL,
)

__all__ = [
    "engine",
    "SessionLocal",
    "Base",
    "get_db",
    "get_database_url",
    "DATABASE_URL",
]
