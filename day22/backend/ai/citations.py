"""
Product Citation Extractor and Validator
Formats and deduplicates citations based on documents retrieved from the vector store.
"""
from __future__ import annotations

from typing import Any


def format_citations_from_retrieved(
    retrieved_docs: list[dict[str, Any]]
) -> list[dict[str, Any]]:
    """
    Extract, normalize, and deduplicate citation metadata from retrieved Chroma documents.
    Only returns products that were actually present in the retrieved context.
    """
    seen_ids: set[int] = set()
    citations: list[dict[str, Any]] = []

    for item in retrieved_docs:
        meta = item.get("metadata", {})
        pid = meta.get("product_id")
        if not pid or pid in seen_ids:
            continue

        try:
            pid_int = int(pid)
        except (ValueError, TypeError):
            continue

        seen_ids.add(pid_int)
        citations.append({
            "product_id": pid_int,
            "product_name": str(meta.get("product_name", f"Product #{pid_int}")),
            "category": str(meta.get("category", "General")),
            "price": float(meta.get("price", 0.0)),
            "stock": int(meta.get("stock", 0)),
            "url": str(meta.get("url") or f"/products/{pid_int}"),
        })

    return citations
