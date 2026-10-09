"""
Backward-compatibility adapter for database module.
Re-exports from app.db.database.
"""
from app.db.database import (
    database_connection,
    initialize_database,
    _detect_engine,
    ForeignKeyViolation,
    UniqueViolation,
    DEFAULT_CATALOG,
)

__all__ = [
    "database_connection",
    "initialize_database",
    "_detect_engine",
    "ForeignKeyViolation",
    "UniqueViolation",
    "DEFAULT_CATALOG",
]
