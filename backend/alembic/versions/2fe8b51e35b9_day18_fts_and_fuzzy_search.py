"""day18_fts_and_fuzzy_search

Revision ID: 2fe8b51e35b9
Revises: 
Create Date: 2026-10-08 11:47:07.528572

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '2fe8b51e35b9'
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema with pg_trgm, description, stock, tsvector, and GIN indexes."""
    conn = op.get_bind()
    dialect = conn.dialect.name

    if dialect == "postgresql":
        op.execute("CREATE EXTENSION IF NOT EXISTS pg_trgm;")
        op.execute("ALTER TABLE products ADD COLUMN IF NOT EXISTS description TEXT DEFAULT '';")
        op.execute("ALTER TABLE products ADD COLUMN IF NOT EXISTS stock INTEGER DEFAULT 50;")
        
        # Check if search_vector column exists before adding
        op.execute("""
            DO $$
            BEGIN
                IF NOT EXISTS (
                    SELECT 1 FROM information_schema.columns 
                    WHERE table_name = 'products' AND column_name = 'search_vector'
                ) THEN
                    ALTER TABLE products ADD COLUMN search_vector tsvector
                    GENERATED ALWAYS AS (
                        to_tsvector('english', coalesce(name, '') || ' ' || coalesce(description, '') || ' ' || coalesce(category, ''))
                    ) STORED;
                END IF;
            END
            $$;
        """)

        op.execute("CREATE INDEX IF NOT EXISTS products_search_vector_gin_idx ON products USING GIN (search_vector);")
        op.execute("CREATE INDEX IF NOT EXISTS products_name_trgm_gin_idx ON products USING GIN (name gin_trgm_ops);")
        op.execute("CREATE INDEX IF NOT EXISTS products_category_trgm_gin_idx ON products USING GIN (category gin_trgm_ops);")
        op.execute("CREATE INDEX IF NOT EXISTS products_desc_trgm_gin_idx ON products USING GIN (description gin_trgm_ops);")
    else:
        # SQLite fallback
        try:
            op.execute("ALTER TABLE products ADD COLUMN description TEXT DEFAULT '';")
        except Exception:
            pass
        try:
            op.execute("ALTER TABLE products ADD COLUMN stock INTEGER DEFAULT 50;")
        except Exception:
            pass


def downgrade() -> None:
    """Downgrade schema."""
    conn = op.get_bind()
    if conn.dialect.name == "postgresql":
        op.execute("DROP INDEX IF EXISTS products_desc_trgm_gin_idx;")
        op.execute("DROP INDEX IF EXISTS products_category_trgm_gin_idx;")
        op.execute("DROP INDEX IF EXISTS products_name_trgm_gin_idx;")
        op.execute("DROP INDEX IF EXISTS products_search_vector_gin_idx;")
        op.execute("ALTER TABLE products DROP COLUMN IF EXISTS search_vector;")
        op.execute("ALTER TABLE products DROP COLUMN IF EXISTS stock;")
        op.execute("ALTER TABLE products DROP COLUMN IF EXISTS description;")
