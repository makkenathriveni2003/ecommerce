"""
Day 22 Interactive AI Quickstart CLI
Allows direct testing of RAG Chat, Semantic Search, Description Generator, and Cost Governance.
"""
import sys
import os
import asyncio
import json

# Safe console reconfig
if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)
if os.path.join(PROJECT_ROOT, "backend") not in sys.path:
    sys.path.insert(0, os.path.join(PROJECT_ROOT, "backend"))

async def test_semantic_search(query: str = "casual footwear for running"):
    print(f"\n--- [1] Semantic Vector Search (ChromaDB) ---")
    print(f"Query: \"{query}\"")
    from app.services.ai.vector_store import ChromaVectorStore
    store = ChromaVectorStore()
    results = store.query_similar(query=query, top_k=3)
    print(f"Found {len(results)} semantically matched items:")
    for idx, item in enumerate(results, 1):
        meta = item.get("metadata", {})
        print(f"  {idx}. {meta.get('name', 'Product')} (Category: {meta.get('category')}, Price: Rs. {meta.get('price')})")
    print()

async def test_description_generator():
    print(f"--- [2] AI Product Description Generator (with Redis Caching) ---")
    from app.services.ai.description_generator import generate_ai_product_description
    res = await generate_ai_product_description(
        name="Handcrafted Leather Oxford Shoes",
        category="Footwear",
        price=3499.0,
        keywords=["Genuine Full-Grain Leather", "Cushioned Orthopedic Footbed", "Handcrafted in India"]
    )
    print("Generated E-Commerce Copy:")
    print(res.get("description", ""))
    print("\nKey Bullet Points:")
    for bullet in res.get("bullet_points", []):
        print(f"  * {bullet}")
    print()

def test_cost_governance():
    print(f"--- [3] Cost Governance & Redis Cache Stats ---")
    from app.services.ai.ai_cache import ai_cache
    metrics = ai_cache.get_governance_metrics()
    for k, v in metrics.items():
        print(f"  {k.replace('_', ' ').title()}: {v}")
    print()

async def main():
    print("=" * 70)
    print("  DAY 22: AI QUICKSTART DEMO (GenZ Zone / Chow Zoon)")
    print("=" * 70)
    await test_semantic_search()
    await test_description_generator()
    test_cost_governance()
    print("=" * 70)

if __name__ == "__main__":
    asyncio.run(main())
