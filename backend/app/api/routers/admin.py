import time
import uuid
import logging
from datetime import datetime, timezone
from typing import Any, List
from fastapi import APIRouter, Depends, File, HTTPException, UploadFile

from ...core.config import settings
from ...core.security import require_admin, require_authenticated_user
from ...db.database import database_connection
from ...schemas.schemas import BulkImportResponse, OrderStatusData, ProductData
from ...services.order_service import (
    attach_order_items,
    get_sqlalchemy_orders_optimized,
)
from ...services.product_service import (
    create_product,
    delete_product,
    get_products,
    update_product,
)
from ...services.websocket_manager import websocket_manager
from ...tasks.celery_tasks import bulk_import_products_csv_task

logger = logging.getLogger("shopzone_admin_router")
router = APIRouter(prefix="/admin", tags=["Admin"], dependencies=[Depends(require_admin)])


@router.get("/products")
def get_admin_products() -> list[dict[str, object]]:
    return get_products(skip=0, limit=200)


@router.post("/products")
def admin_create_product(product: ProductData) -> dict[str, object]:
    return create_product(product)


@router.put("/products/{product_id}")
def admin_update_product(product_id: int, product: ProductData) -> dict[str, object]:
    return update_product(product_id, product)


@router.delete("/products/{product_id}")
def admin_delete_product(product_id: int) -> dict[str, object]:
    return delete_product(product_id)


@router.post("/products/import-csv", response_model=BulkImportResponse)
async def admin_import_products_csv(
    file: UploadFile = File(...),
    user: dict[str, Any] = Depends(require_authenticated_user),
) -> dict[str, Any]:
    if not file.filename or not file.filename.lower().endswith(".csv"):
        raise HTTPException(
            status_code=400,
            detail="Invalid file format. Please upload a valid .csv file.",
        )

    unique_name = f"import_{int(time.time())}_{uuid.uuid4().hex[:8]}.csv"
    temp_path = settings.TEMP_CSV_DIR / unique_name

    try:
        content = await file.read()
        if not content or len(content.strip()) == 0:
            raise HTTPException(status_code=400, detail="Uploaded CSV file is empty.")
        temp_path.write_bytes(content)
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to save uploaded CSV: %s", e)
        raise HTTPException(status_code=500, detail=f"Failed to save uploaded CSV: {str(e)}")

    task = bulk_import_products_csv_task.delay(str(temp_path), user["email"])
    logger.info("Queued bulk CSV import task %s for file %s by %s", task.id, file.filename, user["email"])

    return {
        "success": True,
        "task_id": task.id,
        "status": "PENDING",
        "filename": file.filename,
        "message": f"CSV import queued with task ID {task.id}",
    }


@router.get("/orders")
def get_admin_orders() -> list[dict[str, object]]:
    with database_connection() as connection:
        orders = connection.execute(
            """
            SELECT id, user_id, email, status, total, created_at, full_name,
                   phone, address, city, state, pincode, payment_method
            FROM orders
            ORDER BY created_at DESC, id DESC
            """
        ).fetchall()
        return attach_order_items(connection, orders)


@router.get("/orders/optimized")
def get_admin_orders_optimized() -> list[dict[str, Any]]:
    """Optimized admin orders using SQLAlchemy selectinload + joinedload (2 queries total)."""
    return get_sqlalchemy_orders_optimized(user_id=None)


@router.patch("/orders/{order_id}/status")
async def update_order_status(
    order_id: int,
    data: OrderStatusData,
) -> dict[str, object]:
    with database_connection() as connection:
        row = connection.execute(
            """
            UPDATE orders
            SET status = %s
            WHERE id = %s
            RETURNING id, status, total, email, user_id
            """,
            (data.status, order_id),
        ).fetchone()
    if row is None:
        raise HTTPException(status_code=404, detail="Order not found")

    order_info = dict(row)
    customer_email = order_info.get("email", "").lower()

    # Real-time WebSocket Order update broadcast
    order_event = {
        "order_id": order_id,
        "status": data.status,
        "email": customer_email,
        "total": order_info.get("total", 0.0),
        "user_id": order_info.get("user_id"),
        "updated_at": datetime.now(timezone.utc).isoformat(),
        "message": f"Order #{order_id} status updated to {data.status}.",
    }
    await websocket_manager.broadcast_order_update(order_event, customer_email)

    # Real-time Notification broadcast
    notification_title_map = {
        "pending": "Order Confirmed",
        "processing": "Order Processing",
        "shipped": "Order Shipped",
        "delivered": "Order Delivered",
        "cancelled": "Order Cancelled",
    }
    title = notification_title_map.get(data.status, f"Order {data.status.capitalize()}")
    notification_data = {
        "id": f"notif-order-{order_id}-{data.status}-{int(time.time()*1000)}",
        "order_id": order_id,
        "title": title,
        "message": f"Your order #{order_id} status is now {data.status}.",
        "type": data.status,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "read": False,
    }
    await websocket_manager.broadcast_notification(notification_data, customer_email)

    return {
        "success": True,
        "message": "Order status updated",
        "order": {"id": order_id, "status": data.status},
    }
