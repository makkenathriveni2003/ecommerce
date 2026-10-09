from typing import Any, Dict, List, Optional
from datetime import datetime, timezone
from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.orm import selectinload, joinedload

from ..db.database import database_connection, _detect_engine
from ..db.session import SessionLocal
from ..models.models import Order as SqlAlchemyOrder, OrderItem as SqlAlchemyOrderItem
from ..schemas.schemas import OrderData


def order_items_for_orders(
    connection: Any,
    order_ids: list[int],
) -> dict[int, list[dict[str, object]]]:
    if not order_ids:
        return {}
    engine_name = _detect_engine()
    if engine_name == "postgres":
        rows = connection.execute(
            """
            SELECT item.order_id, item.id, item.product_id,
                   COALESCE(item.product_name, product.name) AS name,
                   item.quantity, item.unit_price
            FROM order_items AS item
            JOIN products AS product ON product.id = item.product_id
            WHERE item.order_id = ANY(%s)
            ORDER BY item.order_id, item.id
            """,
            (order_ids,),
        ).fetchall()
    else:
        placeholders = ", ".join(["?"] * len(order_ids))
        rows = connection.execute(
            f"""
            SELECT item.order_id, item.id, item.product_id,
                   COALESCE(item.product_name, product.name) AS name,
                   item.quantity, item.unit_price
            FROM order_items AS item
            JOIN products AS product ON product.id = item.product_id
            WHERE item.order_id IN ({placeholders})
            ORDER BY item.order_id, item.id
            """,
            order_ids,
        ).fetchall()
    result: dict[int, list[dict[str, object]]] = {}
    for row in rows:
        item = dict(row)
        order_id = item.pop("order_id")
        result.setdefault(order_id, []).append(item)
    return result


def attach_order_items(
    connection: Any,
    orders: list[dict[str, Any]],
) -> list[dict[str, object]]:
    order_ids = [order["id"] for order in orders]
    items_by_order = order_items_for_orders(connection, order_ids)
    return [
        {**dict(order), "items": items_by_order.get(order["id"], [])}
        for order in orders
    ]


def get_sqlalchemy_orders_optimized(user_id: int | None = None) -> list[dict[str, Any]]:
    """Eager-loads orders, items, and products in exactly 2 SQL queries using selectinload + joinedload."""
    db = SessionLocal()
    try:
        stmt = (
            select(SqlAlchemyOrder)
            .options(
                selectinload(SqlAlchemyOrder.items).joinedload(SqlAlchemyOrderItem.product)
            )
            .order_by(SqlAlchemyOrder.created_at.desc(), SqlAlchemyOrder.id.desc())
        )
        if user_id is not None:
            stmt = stmt.where(SqlAlchemyOrder.user_id == user_id)
        orders = db.execute(stmt).scalars().all()
        return [o.to_dict() for o in orders]
    finally:
        db.close()


def create_new_order(order: OrderData, user: dict[str, Any]) -> dict[str, Any]:
    details = {
        field: getattr(order, field).strip()
        for field in (
            "full_name",
            "email",
            "phone",
            "address",
            "city",
            "state",
            "pincode",
            "payment_method",
        )
    }
    if any(not value for value in details.values()):
        raise HTTPException(
            status_code=422, detail="Order contact and delivery fields are required"
        )
    if "@" not in details["email"]:
        raise HTTPException(status_code=422, detail="A valid order email is required")

    product_ids = sorted({item.product_id for item in order.items})
    with database_connection() as connection:
        products = connection.execute(
            """
            SELECT id, name, price
            FROM products
            WHERE id = ANY(%s)
            ORDER BY id
            FOR SHARE
            """,
            (product_ids,),
        ).fetchall()
        product_map = {product["id"]: product for product in products}
        if len(product_map) != len(product_ids):
            raise HTTPException(
                status_code=404, detail="One or more products were not found"
            )

        total = sum(
            (product_map[item.product_id]["price"] * item.quantity for item in order.items),
            0.0,
        )
        order_row = connection.execute(
            """
            INSERT INTO orders (
                user_id, email, total, status, full_name, phone, address,
                city, state, pincode, payment_method
            )
            VALUES (%s, %s, %s, 'pending', %s, %s, %s, %s, %s, %s, %s)
            RETURNING id, status, total, created_at
            """,
            (
                user["id"],
                details["email"].lower(),
                total,
                details["full_name"],
                details["phone"],
                details["address"],
                details["city"],
                details["state"],
                details["pincode"],
                details["payment_method"],
            ),
        ).fetchone()
        if order_row is None:
            raise RuntimeError("The database did not return the new order")
        order_id = order_row["id"]
        for item in order.items:
            connection.execute(
                """
                INSERT INTO order_items (
                    order_id, product_id, product_name, quantity, unit_price
                )
                VALUES (%s, %s, %s, %s, %s)
                """,
                (
                    order_id,
                    item.product_id,
                    product_map[item.product_id]["name"],
                    item.quantity,
                    product_map[item.product_id]["price"],
                ),
            )
        item_rows = order_items_for_orders(connection, [order_id])

    result_order = dict(order_row)
    result_order["items"] = item_rows.get(order_id, [])
    result_order["user_id"] = user["id"]
    result_order["email"] = details["email"].lower()
    return result_order
