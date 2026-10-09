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
    return [dict(row) for row in rows]


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
    return dict(row)


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
    return dict(row)


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
