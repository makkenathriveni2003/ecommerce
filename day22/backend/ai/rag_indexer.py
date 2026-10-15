"""
RAG Product Catalog Indexer
Loads actual ShopZone products from PostgreSQL / SQLite,
chunks them with LangChain's RecursiveCharacterTextSplitter,
and indexes them with metadata into ChromaDB.
"""
from __future__ import annotations

import logging
from typing import Any

from langchain_text_splitters import RecursiveCharacterTextSplitter

from ...core.config import settings
from ...db.database import database_connection
from .vector_store import ChromaVectorStore

logger = logging.getLogger("shopzone_ai.indexer")


class CatalogIndexer:
    """
    Indexes and synchronizes ShopZone database products into ChromaDB.
    """

    def __init__(self, vector_store: ChromaVectorStore | None = None):
        self.vector_store = vector_store or ChromaVectorStore()
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=settings.RAG_CHUNK_SIZE,
            chunk_overlap=settings.RAG_CHUNK_OVERLAP,
            separators=["\n\n", "\n", ". ", " ", ""],
        )

    def _format_product_document(self, product: dict[str, Any]) -> str:
        """
        Format a product record into a rich, structured text document for embedding.
        Never includes sensitive customer or transactional data.
        """
        pid = product.get("id")
        name = product.get("name", "Unknown Product")
        category = product.get("category", "General")
        price = product.get("price", 0.0)
        stock = product.get("stock", 50)
        desc = (product.get("description") or "").strip()

        stock_text = f"In Stock ({stock} units available)" if (stock and stock > 0) else "Out of Stock"

        doc = (
            f"Product ID: {pid}\n"
            f"Product Name: {name}\n"
            f"Category: {category}\n"
            f"Price: ₹{price:,.2f} INR\n"
            f"Availability: {stock_text}\n"
        )
        if desc:
            doc += f"Description: {desc}\n"
        return doc

    def index_single_product(self, product: dict[str, Any]) -> int:
        """
        Index or update a single product record.
        Avoids duplicates by using deterministic chunk IDs.
        """
        pid = product.get("id")
        if not pid:
            return 0

        full_text = self._format_product_document(product)
        chunks = self.text_splitter.split_text(full_text)
        if not chunks:
            chunks = [full_text]

        documents = []
        metadatas = []
        ids = []

        for idx, chunk in enumerate(chunks):
            chunk_id = f"prod_{pid}_chunk_{idx}"
            documents.append(chunk)
            metadatas.append({
                "product_id": pid,
                "product_name": str(product.get("name", "")),
                "category": str(product.get("category", "")),
                "price": float(product.get("price", 0.0)),
                "stock": int(product.get("stock", 0) or 0),
                "url": f"/products/{pid}",
                "chunk_index": idx,
            })
            ids.append(chunk_id)

        return self.vector_store.upsert_documents(documents, metadatas, ids)

    def reindex_all_products(self, clear_existing: bool = True) -> dict[str, Any]:
        """
        Load all product records from the existing database and index them into ChromaDB.
        Safe for initial indexing and scheduled / manual re-indexing.
        """
        logger.info("Starting catalog reindexing (clear_existing=%s)...", clear_existing)
        if clear_existing:
            self.vector_store.clear()

        products: list[dict[str, Any]] = []
        with database_connection() as connection:
            rows = connection.execute(
                "SELECT id, name, price, category, image, description, stock FROM products ORDER BY id ASC"
            ).fetchall()
            products = [dict(r) for r in rows]

        if not products:
            logger.warning("No products found in the database to index.")
            return {
                "products_indexed": 0,
                "chunks_indexed": 0,
                "total_vectors": self.vector_store.count(),
                "message": "Catalogue is empty; 0 products indexed.",
            }

        all_documents: list[str] = []
        all_metadatas: list[dict[str, Any]] = []
        all_ids: list[str] = []

        for p in products:
            pid = p["id"]
            full_text = self._format_product_document(p)
            chunks = self.text_splitter.split_text(full_text)
            if not chunks:
                chunks = [full_text]

            for idx, chunk in enumerate(chunks):
                chunk_id = f"prod_{pid}_chunk_{idx}"
                all_documents.append(chunk)
                all_metadatas.append({
                    "product_id": pid,
                    "product_name": str(p.get("name", "")),
                    "category": str(p.get("category", "")),
                    "price": float(p.get("price", 0.0)),
                    "stock": int(p.get("stock", 0) or 0),
                    "url": f"/products/{pid}",
                    "chunk_index": idx,
                })
                all_ids.append(chunk_id)

        # Batch upsert into ChromaDB
        BATCH_SIZE = 50
        total_chunks = 0
        for i in range(0, len(all_ids), BATCH_SIZE):
            batch_docs = all_documents[i : i + BATCH_SIZE]
            batch_metas = all_metadatas[i : i + BATCH_SIZE]
            batch_ids = all_ids[i : i + BATCH_SIZE]
            total_chunks += self.vector_store.upsert_documents(batch_docs, batch_metas, batch_ids)

        logger.info(
            "Successfully indexed %d products (%d chunks) into ChromaDB.",
            len(products),
            total_chunks,
        )
        return {
            "products_indexed": len(products),
            "chunks_indexed": total_chunks,
            "total_vectors": self.vector_store.count(),
            "message": f"Successfully indexed {len(products)} products ({total_chunks} chunks).",
        }
