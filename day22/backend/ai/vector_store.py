""""""
ChromaDB Vector Store Manager
Encapsulates vector persistence, collection lifecycle, and similarity search for ShopZone RAG.
"""
from __future__ import annotations

import logging
from typing import Any

import chromadb
from chromadb.config import Settings as ChromaSettings

from ...core.config import settings
from .embeddings import BaseEmbeddingProvider, get_embedding_provider

logger = logging.getLogger("shopzone_ai.vector_store")


class ChromaVectorStore:
    """
    Thread-safe ChromaDB persistent client wrapper.
    Keeps vector storage details isolated from the rest of the application.
    """

    COLLECTION_NAME = "shopzone_products"

    def __init__(
        self,
        persist_dir: str | None = None,
        embedding_provider: BaseEmbeddingProvider | None = None,
    ):
        self.persist_dir = str(persist_dir or settings.CHROMA_PERSIST_DIR)
        self.embedding_provider = embedding_provider or get_embedding_provider()
        self._client: chromadb.ClientAPI | None = None
        self._collection = None

    def _get_client(self) -> chromadb.ClientAPI:
        if self._client is None:
            self._client = chromadb.PersistentClient(
                path=self.persist_dir,
                settings=ChromaSettings(anonymized_telemetry=False, is_persistent=True),
            )
        return self._client

    def _get_collection(self):
        if self._collection is None:
            client = self._get_client()
            self._collection = client.get_or_create_collection(
                name=self.COLLECTION_NAME,
                metadata={"description": "ShopZone E-Commerce Product Catalog Vectors"},
            )
        return self._collection

    def count(self) -> int:
        """Return the number of indexed document chunks in the vector store."""
        try:
            return self._get_collection().count()
        except Exception as exc:
            logger.error("Failed to count vectors: %s", exc)
            return 0

    def upsert_documents(
        self,
        documents: list[str],
        metadatas: list[dict[str, Any]],
        ids: list[str],
    ) -> int:
        """
        Upsert document chunks and their embeddings into ChromaDB.
        Idempotent: updates existing IDs or inserts new ones.
        """
        if not documents:
            return 0

        # Sanitize metadata values: ChromaDB requires primitive types (str, int, float, bool)
        clean_metadatas = []
        for meta in metadatas:
            clean = {}
            for k, v in meta.items():
                if isinstance(v, (str, int, float, bool)):
                    clean[k] = v
                elif v is None:
                    clean[k] = ""
                else:
                    clean[k] = str(v)
            clean_metadatas.append(clean)

        embeddings = self.embedding_provider.embed_documents(documents)
        collection = self._get_collection()
        collection.upsert(
            ids=ids,
            embeddings=embeddings,
            documents=documents,
            metadatas=clean_metadatas,
        )
        logger.info("Upserted %d document chunks into ChromaDB", len(ids))
        return len(ids)

    def query_similar(
        self,
        query: str,
        top_k: int = 4,
        where_filter: dict[str, Any] | None = None,
    ) -> list[dict[str, Any]]:
        """
        Search for top_k most relevant product documents for a user query.
        Returns normalized list of dictionaries containing:
        - document: str
        - metadata: dict
        - distance: float
        - id: str
        """
        if not query.strip() or self.count() == 0:
            return []

        query_embedding = self.embedding_provider.embed_query(query)
        collection = self._get_collection()

        try:
            results = collection.query(
                query_embeddings=[query_embedding],
                n_results=min(top_k, max(1, self.count())),
                where=where_filter,
                include=["documents", "metadatas", "distances"],
            )
        except Exception as exc:
            logger.warning("Vector search query error: %s", exc)
            return []

        retrieved: list[dict[str, Any]] = []
        ids = results.get("ids", [[]])[0]
        docs = results.get("documents", [[]])[0]
        metas = results.get("metadatas", [[]])[0]
        distances = results.get("distances", [[]])[0]

        for i in range(len(ids)):
            retrieved.append({
                "id": ids[i],
                "document": docs[i] if i < len(docs) else "",
                "metadata": metas[i] if i < len(metas) else {},
                "distance": distances[i] if i < len(distances) else 1.0,
            })

        return retrieved

    def clear(self) -> None:
        """Clear all indexed documents from the collection."""
        try:
            client = self._get_client()
            client.delete_collection(self.COLLECTION_NAME)
            self._collection = None
            logger.info("Cleared ChromaDB collection '%s'", self.COLLECTION_NAME)
        except Exception as exc:
            logger.warning("Failed to clear ChromaDB collection: %s", exc)
