import logging
import os
import shutil
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from fastapi import APIRouter, Depends, HTTPException, Query, Request
from fastapi.responses import FileResponse
from fastapi.security import HTTPAuthorizationCredentials

from ...core.config import settings
from ...core.rate_limit import limiter
from ...core.security import (
    bearer_scheme,
    read_access_token,
    require_authenticated_user,
    verify_object_ownership,
)
from ...db.database import database_connection
from ...schemas.schemas import OrderData
from ...services.order_service import (
    attach_order_items,
    create_new_order,
    get_sqlalchemy_orders_optimized,
)
from ...services.websocket_manager import websocket_manager
from ...tasks.celery_tasks import INVOICE_DIR, generate_invoice_pdf_task

router = APIRouter(prefix="/orders", tags=["Orders"])


@router.post("")
@router.post("/")
@limiter.limit(settings.ORDER_RATE_LIMIT)
async def create_order(
    request: Request,
    order: OrderData,
    user: dict[str, Any] = Depends(require_authenticated_user),
) -> dict[str, object]:
    result_order = create_new_order(order, user)
    order_id = result_order["id"]
    customer_email = result_order["email"]

    # Real-time WebSocket event broadcast
    order_event = {
        "order_id": order_id,
        "user_id": user["id"],
        "email": customer_email,
        "status": "pending",
        "total": result_order["total"],
        "created_at": str(result_order.get("created_at", "")),
        "items": result_order.get("items", []),
        "message": f"Order #{order_id} placed successfully.",
    }
    await websocket_manager.broadcast_order_update(order_event, customer_email)

    # Notification event broadcast
    notification_data = {
        "id": f"notif-order-{order_id}-{int(time.time()*1000)}",
        "order_id": order_id,
        "title": "Order Confirmed",
        "message": f"Your order #{order_id} has been confirmed.",
        "type": "confirmed",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "read": False,
    }
    await websocket_manager.broadcast_notification(notification_data, customer_email)

    return {
        "success": True,
        "message": "Order placed successfully",
        "order": result_order,
    }


@router.get("")
@router.get("/")
def get_order_history(
    user: dict[str, Any] = Depends(require_authenticated_user),
) -> list[dict[str, object]]:
    with database_connection() as connection:
        orders = connection.execute(
            """
            SELECT id, status, total, created_at
            FROM orders
            WHERE user_id = %s
            ORDER BY created_at DESC, id DESC
            """,
            (user["id"],),
        ).fetchall()
        return attach_order_items(connection, orders)


@router.get("/optimized")
def get_order_history_optimized(
    token: str | None = Query(default=None),
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
) -> list[dict[str, Any]]:
    """Optimized order history using SQLAlchemy selectinload + joinedload (2 queries total)."""
    auth_token = None
    if credentials:
        auth_token = credentials.credentials
    elif token:
        auth_token = token

    user_id = None
    if auth_token:
        try:
            email = read_access_token(auth_token)
            with database_connection() as conn:
                u = conn.execute("SELECT id FROM users WHERE email = %s", (email,)).fetchone()
                if u:
                    user_id = u["id"]
        except Exception:
            pass

    return get_sqlalchemy_orders_optimized(user_id=user_id)


@router.post("/{order_id}/invoice")
def generate_order_invoice(
    order_id: int,
    user: dict[str, Any] = Depends(require_authenticated_user),
) -> dict[str, Any]:
    with database_connection() as connection:
        order = connection.execute(
            "SELECT id, user_id, email FROM orders WHERE id = %s",
            (order_id,),
        ).fetchone()
    if order is None:
        raise HTTPException(status_code=404, detail="Order not found")

    # OWASP BOLA / IDOR protection
    if user["role"] != "admin" and order["user_id"] != user["id"] and order["email"].lower() != user["email"].lower():
        raise HTTPException(status_code=403, detail="You do not have permission to generate this invoice")

    task = generate_invoice_pdf_task.delay(order_id=order_id, user_email=user["email"])

    return {
        "success": True,
        "task_id": task.id,
        "order_id": order_id,
        "status": "PENDING",
        "message": f"Invoice generation task queued for Order #{order_id}",
    }


logger = logging.getLogger("orders_router")


@router.get("/{order_id}/invoice/download")
def download_order_invoice(
    order_id: int,
    token: str | None = Query(default=None),
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
) -> FileResponse:
    auth_token = None
    if credentials:
        auth_token = credentials.credentials
    elif token:
        auth_token = token

    with database_connection() as connection:
        order = connection.execute(
            "SELECT id, user_id, email FROM orders WHERE id = %s",
            (order_id,),
        ).fetchone()
        if not order:
            raise HTTPException(status_code=404, detail="Order not found")

        if auth_token:
            try:
                email = read_access_token(auth_token)
                user = connection.execute(
                    "SELECT id, email, role FROM users WHERE email = %s",
                    (email,),
                ).fetchone()
                if user and user["role"] != "admin" and order["user_id"] != user["id"] and str(order.get("email", "")).lower() != str(user["email"]).lower():
                    raise HTTPException(status_code=403, detail="You do not have access to this invoice")
            except HTTPException:
                raise
            except Exception:
                pass

    file_name = f"ShopZone_Invoice_{int(order_id)}.pdf"
    file_path = (INVOICE_DIR / file_name).resolve()

    # If file not in current INVOICE_DIR, search candidate locations
    if not file_path.exists():
        candidate_dirs = [
            Path("C:/Users/Dell/Downloads/day19/backend/generated_invoices"),
            Path("C:/Users/Dell/Downloads/day9-fastapi/backend/generated_invoices"),
            Path.cwd() / "backend" / "generated_invoices",
            Path.cwd() / "generated_invoices",
            settings.BASE_DIR / "generated_invoices",
        ]
        for candidate_dir in candidate_dirs:
            candidate_file = (candidate_dir / file_name).resolve()
            if candidate_file.exists():
                file_path = candidate_file
                try:
                    INVOICE_DIR.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(candidate_file, INVOICE_DIR / file_name)
                except Exception:
                    pass
                break

    # If still not found, generate on-demand using ReportLab task logic
    if not file_path.exists():
        try:
            generate_invoice_pdf_task(order_id)
            if (INVOICE_DIR / file_name).exists():
                file_path = (INVOICE_DIR / file_name).resolve()
            else:
                for candidate_dir in [
                    Path("C:/Users/Dell/Downloads/day19/backend/generated_invoices"),
                    Path("C:/Users/Dell/Downloads/day9-fastapi/backend/generated_invoices"),
                ]:
                    cand = (candidate_dir / file_name).resolve()
                    if cand.exists():
                        file_path = cand
                        break
        except Exception as gen_err:
            logger.warning("On-demand invoice generation fallback failed: %s", gen_err)

    if not file_path.exists():
        raise HTTPException(status_code=404, detail="Invoice PDF not found. Please generate it first.")

    return FileResponse(
        path=str(file_path),
        media_type="application/pdf",
        filename=file_name,
        headers={"Content-Disposition": f'attachment; filename="{file_name}"'},
    )
