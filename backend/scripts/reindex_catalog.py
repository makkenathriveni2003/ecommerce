"""
CLI Script to Reindex ShopZone Product Catalog into ChromaDB
Usage:
    python backend/scripts/reindex_catalog.py
"""
import sys
from pathlib import Path

# Add backend directory to sys.path
backend_dir = Path(__file__).resolve().parent.parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

from app.db.database import initialize_database
from app.services.ai import CatalogIndexer, ChromaVectorStore


def main():
    print("=" * 60)
    print("ShopZone Catalog Vector Reindexing Tool")
    print("=" * 60)

    print("Step 1: Initializing database connection...")
    initialize_database()

    print("Step 2: Connecting to ChromaDB vector store...")
    store = ChromaVectorStore()
    indexer = CatalogIndexer(vector_store=store)

    print(f"Current vectors in ChromaDB: {store.count()}")
    print("Step 3: Indexing products from database...")
    result = indexer.reindex_all_products(clear_existing=True)

    print("-" * 60)
    print(f"Indexed Products: {result['products_indexed']}")
    print(f"Total Chunks:     {result['chunks_indexed']}")
    print(f"Total Vectors:    {result['total_vectors']}")
    print(f"Status:           {result['message']}")
    print("=" * 60)


if __name__ == "__main__":
    main()
