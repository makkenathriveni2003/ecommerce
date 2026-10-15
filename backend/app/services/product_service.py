from typing import Any, Dict, List
from fastapi import HTTPException
from ..db.database import database_connection, _detect_engine, ForeignKeyViolation
from ..schemas.schemas import ProductData


def clean_product(product: ProductData) -> tuple[str, float, str, str, str, int]:
    name = product.name.strip()
    category = product.category.strip()
    image = product.image.strip()
    description = (product.description or "").strip()
    stock = product.stock if product.stock is not None else 50
    if not name or not category or not image:
        raise HTTPException(status_code=422, detail="Product fields cannot be blank")
    return name, product.price, category, image, description, stock


def get_products(
    skip: int = 0,
    limit: int = 100,
    search: str | None = None,
) -> List[Dict[str, Any]]:
    engine_name = _detect_engine()
    with database_connection() as connection:
        if search and search.strip():
            q = search.strip()
            term = f"%{q.lower()}%"
            if engine_name == "postgres":
                rows = connection.execute(
                    """
                    SELECT id, name, price, category, image,
                           COALESCE(description, '') AS description,
                           COALESCE(stock, 50) AS stock,
                           ts_rank(search_vector, plainto_tsquery('english', %s)) AS ft_rank,
                           GREATEST(similarity(name, %s), word_similarity(%s, name)) AS fuzzy_sim
                    FROM products
                    WHERE search_vector @@ plainto_tsquery('english', %s)
                       OR similarity(name, %s) > 0.2
                       OR word_similarity(%s, name) > 0.3
                       OR similarity(category, %s) > 0.25
                       OR LOWER(name) LIKE %s
                       OR LOWER(category) LIKE %s
                    ORDER BY 
                       (ts_rank(search_vector, plainto_tsquery('english', %s)) * 3.0 + 
                        GREATEST(similarity(name, %s), word_similarity(%s, name)) * 2.0) DESC,
                       id ASC
                    LIMIT %s OFFSET %s
                    """,
                    (q, q, q, q, q, q, q, term, term, q, q, q, limit, skip),
                ).fetchall()
            else:
                rows = connection.execute(
                    """
                    SELECT id, name, price, category, image,
                           COALESCE(description, '') AS description,
                           COALESCE(stock, 50) AS stock
                    FROM products
                    WHERE LOWER(name) LIKE %s OR LOWER(category) LIKE %s OR LOWER(COALESCE(description, '')) LIKE %s
                    ORDER BY id ASC
                    LIMIT %s OFFSET %s
                    """,
                    (term, term, term, limit, skip),
                ).fetchall()
        else:
            rows = connection.execute(
                """
                SELECT id, name, price, category, image,
                       COALESCE(description, '') AS description,
                       COALESCE(stock, 50) AS stock
                FROM products
                ORDER BY id ASC
                LIMIT %s OFFSET %s
                """,
                (limit, skip),
            ).fetchall()
    unique_products: List[Dict[str, Any]] = []
    seen_names: set[str] = set()
    seen_images: set[str] = set()
    for row in rows:
        d = dict(row)
        name_key = d.get("name", "").strip().lower()
        img_raw = d.get("image", "").strip()
        img_key = img_raw.split("?")[0] if "?" in img_raw else img_raw
        if name_key in seen_names or (img_key and img_key in seen_images):
            continue
        seen_names.add(name_key)
        if img_key:
            seen_images.add(img_key)
        unique_products.append(d)
    return unique_products


def semantic_search_products(query: str, limit: int = 20) -> List[Dict[str, Any]]:
    """
    Search products using ChromaDB embedding-based vector similarity.
    Retrieves semantic matches according to contextual intent and fetches full
    records from PostgreSQL in similarity rank order.
    Gracefully falls back to PostgreSQL full-text/fuzzy search.
    """
    clean_q = query.strip()
    if not clean_q:
        return []

    # Check Redis cache first
    try:
        from .ai.ai_cache import ai_cache
        cached = ai_cache.get_cached_semantic_search(clean_q)
        if cached:
            return cached
    except Exception:
        ai_cache = None

    matched_ids: list[int] = []
    try:
        from .ai import ChromaVectorStore
        store = ChromaVectorStore()
        if store.count() > 0:
            similar_chunks = store.query_similar(query=clean_q, top_k=limit * 2)
            for chunk in similar_chunks:
                meta = chunk.get("metadata", {})
                pid = meta.get("product_id")
                if pid and pid not in matched_ids:
                    try:
                        matched_ids.append(int(pid))
                    except (ValueError, TypeError):
                        pass
                if len(matched_ids) >= limit:
                    break
    except Exception:
        pass

    if matched_ids:
        with database_connection() as connection:
            placeholders = ", ".join(["%s"] * len(matched_ids))
            rows = connection.execute(
                f"""
                SELECT id, name, price, category, image,
                       COALESCE(description, '') AS description,
                       COALESCE(stock, 50) AS stock
                FROM products
                WHERE id IN ({placeholders})
                """,
                tuple(matched_ids),
            ).fetchall()
            row_dict = {r["id"]: dict(r) for r in rows}
            ordered = [row_dict[pid] for pid in matched_ids if pid in row_dict]
            if ordered:
                try:
                    if ai_cache:
                        ai_cache.set_cached_semantic_search(clean_q, ordered)
                except Exception:
                    pass
                return ordered

    # Fallback to full-text / trigram fuzzy search
    fallback_results = get_products(skip=0, limit=limit, search=clean_q)
    try:
        if ai_cache and fallback_results:
            ai_cache.set_cached_semantic_search(clean_q, fallback_results)
    except Exception:
        pass
    return fallback_results


def get_product(product_id: int) -> Dict[str, Any]:
    with database_connection() as connection:
        row = connection.execute(
            """
            SELECT id, name, price, category, image,
                   COALESCE(description, '') AS description,
                   COALESCE(stock, 50) AS stock
            FROM products
            WHERE id = %s
            """,
            (product_id,),
        ).fetchone()
    if row is None:
        raise HTTPException(status_code=404, detail="Product not found")
    return dict(row)


def get_similar_products(product_id: int, limit: int = 4) -> List[Dict[str, Any]]:
    """
    Retrieve smart cross-category styling recommendations ("Complete The Look").
    Instead of showing identical duplicates, recommends matching complementary
    different clothes and accessories (e.g., pairs tops with jeans/sneakers,
    kurtis with heels/handbags/jewellery) just like Amazon and modern shopping apps.
    """
    with database_connection() as connection:
        current_p = connection.execute(
            "SELECT id, category, name FROM products WHERE id = %s",
            (product_id,),
        ).fetchone()

        if not current_p:
            return []

        name = (current_p["name"] or "").lower()
        cat = (current_p["category"] or "").lower()

        is_ethnic_or_dress = any(w in name for w in ["kurti", "anarkali", "dress", "maxi", "skirt"])
        is_top = any(w in name for w in ["hoodie", "tee", "shirt", "vest", "tank", "jacket", "crewneck", "stringer"])
        is_bottom = any(w in name for w in ["jean", "short", "pant", "trouser"])
        is_shoe = "shoe" in cat or any(w in name for w in ["heel", "flat", "sneaker", "pump", "loafer"])
        is_bag = "bag" in cat or any(w in name for w in ["tote", "handbag", "backpack", "satchel"])

        if is_ethnic_or_dress:
            complementary_targets = [
                ("Shoes", ["heel", "flat", "sandal"]),
                ("Bags", ["tote", "handbag", "satchel"]),
                ("Jewellery", ["necklace", "choker", "earring"]),
                ("Accessories", ["watch", "bracelet"]),
            ]
        elif is_top:
            complementary_targets = [
                ("Fashion", ["jean", "short", "pant"]),
                ("Shoes", ["sneaker", "running", "shoe"]),
                ("Bags", ["backpack", "bag"]),
                ("Accessories", ["watch"]),
            ]
        elif is_bottom:
            complementary_targets = [
                ("Fashion", ["tee", "shirt", "hoodie", "vest"]),
                ("Shoes", ["sneaker", "running", "shoe"]),
                ("Bags", ["backpack", "bag"]),
                ("Accessories", ["watch"]),
            ]
        elif is_shoe:
            complementary_targets = [
                ("Fashion", ["dress", "jean", "kurti", "shirt"]),
                ("Bags", ["tote", "handbag", "backpack"]),
                ("Jewellery", ["necklace", "earring", "bracelet"]),
                ("Accessories", ["watch"]),
            ]
        elif is_bag:
            complementary_targets = [
                ("Fashion", ["dress", "kurti", "shirt", "jean"]),
                ("Shoes", ["heel", "flat", "sneaker"]),
                ("Jewellery", ["necklace", "earring"]),
                ("Accessories", ["watch"]),
            ]
        else:
            complementary_targets = [
                ("Fashion", []),
                ("Shoes", []),
                ("Bags", []),
                ("Accessories", []),
            ]

        results = []
        selected_ids = {product_id}

        for target_cat, keywords in complementary_targets:
            if len(results) >= limit:
                break

            query = "SELECT id, name, price, category, image, COALESCE(description, '') as description, COALESCE(stock, 50) as stock FROM products WHERE category = %s AND id != %s"
            params = [target_cat, product_id]

            if keywords:
                kw_clauses = " OR ".join(["name ILIKE %s" for _ in keywords])
                query += f" AND ({kw_clauses})"
                params.extend([f"%{kw}%" for kw in keywords])

            query += " ORDER BY id DESC LIMIT 5"
            rows = connection.execute(query, tuple(params)).fetchall()

            for r in rows:
                if r["id"] not in selected_ids and len(results) < limit:
                    selected_ids.add(r["id"])
                    results.append(dict(r))
                    break

        if len(results) < limit:
            needed = limit - len(results)
            exclude_ids = list(selected_ids)
            placeholders = ", ".join(["%s"] * len(exclude_ids))
            extra = connection.execute(
                f"SELECT id, name, price, category, image, COALESCE(description, '') as description, COALESCE(stock, 50) as stock FROM products WHERE id NOT IN ({placeholders}) ORDER BY id DESC LIMIT %s",
                tuple(exclude_ids + [needed]),
            ).fetchall()
            for r in extra:
                results.append(dict(r))

        return results


def create_product(product: ProductData) -> Dict[str, Any]:
    with database_connection() as connection:
        row = connection.execute(
            """
            INSERT INTO products (name, price, category, image, description, stock)
            VALUES (%s, %s, %s, %s, %s, %s)
            RETURNING id, name, price, category, image, description, stock
            """,
            clean_product(product),
        ).fetchone()
    if row is None:
        raise RuntimeError("The database did not return the new product")
    res = dict(row)
    try:
        from .ai import CatalogIndexer
        CatalogIndexer().index_single_product(res)
    except Exception:
        pass
    return res


def update_product(product_id: int, product: ProductData) -> Dict[str, Any]:
    with database_connection() as connection:
        row = connection.execute(
            """
            UPDATE products
            SET name = %s, price = %s, category = %s, image = %s, description = %s, stock = %s
            WHERE id = %s
            RETURNING id, name, price, category, image, description, stock
            """,
            (*clean_product(product), product_id),
        ).fetchone()
    if row is None:
        raise HTTPException(status_code=404, detail="Product not found")
    res = dict(row)
    try:
        from .ai import CatalogIndexer
        CatalogIndexer().index_single_product(res)
    except Exception:
        pass
    return res


def delete_product(product_id: int) -> Dict[str, Any]:
    try:
        with database_connection() as connection:
            row = connection.execute(
                "DELETE FROM products WHERE id = %s RETURNING id",
                (product_id,),
            ).fetchone()
    except ForeignKeyViolation as error:
        raise HTTPException(
            status_code=409,
            detail="Product cannot be deleted because it is included in an order",
        ) from error
    if row is None:
        raise HTTPException(status_code=404, detail="Product not found")
    return {"success": True, "message": "Product deleted"}
