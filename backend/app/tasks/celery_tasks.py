from __future__ import annotations
import csv
import io
import logging
import os
import shutil
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List

from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.platypus import HRFlowable, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

from .celery_app import celery_app
from ..db.database import database_connection
from ..core.config import settings

logger = logging.getLogger("shopzone_tasks")

INVOICE_DIR = settings.INVOICE_DIR


def _safe_update_state(task_self: Any, state: str = "PROGRESS", meta: dict[str, Any] | None = None) -> None:
    req = getattr(task_self, "request", None)
    if req and getattr(req, "id", None):
        try:
            task_self.update_state(state=state, meta=meta)
        except Exception as err:
            logger.debug("Failed updating task state: %s", err)


@celery_app.task(name="tasks.sample_background_job_task", bind=True)
def sample_background_job_task(self, total_steps: int = 10, step_delay: float = 0.5) -> dict[str, Any]:
    """Sample Celery background task for testing task lifecycle."""
    logger.info("Starting sample background job: %s steps", total_steps)
    for i in range(1, total_steps + 1):
        time.sleep(step_delay)
        percent = int((i / total_steps) * 100)
        _safe_update_state(
            self,
            state="PROGRESS",
            meta={
                "current": i,
                "total": total_steps,
                "percent": percent,
                "message": f"Processing step {i} of {total_steps}...",
                "status": "PROGRESS",
            },
        )
    return {
        "status": "SUCCESS",
        "percent": 100,
        "message": "Sample background task completed successfully!",
        "completed_at": datetime.now(timezone.utc).isoformat(),
    }


@celery_app.task(name="tasks.generate_invoice_pdf_task", bind=True)
def generate_invoice_pdf_task(self, order_id: int, user_email: str | None = None) -> dict[str, Any]:
    """Asynchronously generates a PDF invoice for a given order using ReportLab."""
    logger.info("Generating invoice for order_id=%s", order_id)
    _safe_update_state(
        self,
        state="PROGRESS",
        meta={
            "current": 10,
            "total": 100,
            "percent": 10,
            "message": "Querying order and customer details from database...",
            "status": "PROGRESS",
        },
    )

    with database_connection() as conn:
        order_row = conn.execute(
            """
            SELECT id, user_id, email, total, status, full_name, phone,
                   address, city, state, pincode, payment_method, created_at
            FROM orders
            WHERE id = %s
            """,
            (order_id,),
        ).fetchone()

        if not order_row:
            raise ValueError(f"Order #{order_id} not found")

        order = dict(order_row)

        _safe_update_state(
            self,
            state="PROGRESS",
            meta={
                "current": 35,
                "total": 100,
                "percent": 35,
                "message": "Fetching purchased items and pricing...",
                "status": "PROGRESS",
            },
        )

        item_rows = conn.execute(
            """
            SELECT item.id, item.product_id,
                   COALESCE(item.product_name, product.name, 'Product Item') AS name,
                   item.quantity, item.unit_price
            FROM order_items AS item
            LEFT JOIN products AS product ON product.id = item.product_id
            WHERE item.order_id = %s
            ORDER BY item.id
            """,
            (order_id,),
        ).fetchall()
        items = [dict(r) for r in item_rows]

    _safe_update_state(
        self,
        state="PROGRESS",
        meta={
            "current": 60,
            "total": 100,
            "percent": 60,
            "message": "Composing PDF invoice document with ReportLab...",
            "status": "PROGRESS",
        },
    )

    filename = f"ShopZone_Invoice_{order_id}.pdf"
    file_path = INVOICE_DIR / filename

    doc = SimpleDocTemplate(
        str(file_path),
        pagesize=letter,
        rightMargin=40,
        leftMargin=40,
        topMargin=40,
        bottomMargin=40,
    )

    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        "InvoiceTitle",
        parent=styles["Heading1"],
        fontSize=24,
        leading=28,
        textColor=colors.HexColor("#2563eb"),
        fontName="Helvetica-Bold",
    )
    subtitle_style = ParagraphStyle(
        "InvoiceSubtitle",
        parent=styles["Normal"],
        fontSize=10,
        leading=14,
        textColor=colors.HexColor("#64748b"),
    )
    section_style = ParagraphStyle(
        "InvoiceSection",
        parent=styles["Heading2"],
        fontSize=13,
        leading=16,
        textColor=colors.HexColor("#1e293b"),
        fontName="Helvetica-Bold",
    )
    cell_style = ParagraphStyle(
        "InvoiceCell",
        parent=styles["Normal"],
        fontSize=10,
        leading=13,
        textColor=colors.HexColor("#334155"),
    )
    cell_bold = ParagraphStyle(
        "InvoiceCellBold",
        parent=styles["Normal"],
        fontSize=10,
        leading=13,
        textColor=colors.HexColor("#0f172a"),
        fontName="Helvetica-Bold",
    )

    story = []

    # Header
    header_data = [
        [
            Paragraph("ShopZone", title_style),
            Paragraph(f"<b>INVOICE</b><br/>Invoice #: INV-{order_id:06d}<br/>Date: {str(order.get('created_at', ''))[:10]}", subtitle_style),
        ]
    ]
    header_table = Table(header_data, colWidths=[300, 230])
    header_table.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("ALIGN", (1, 0), (1, 0), "RIGHT"),
    ]))
    story.append(header_table)
    story.append(Spacer(1, 15))
    story.append(HRFlowable(width="100%", thickness=1.5, color=colors.HexColor("#e2e8f0"), spaceBefore=5, spaceAfter=15))

    # Customer & Order Information
    customer_info = [
        [
            Paragraph("<b>Billed To:</b>", section_style),
            Paragraph("<b>Order Details:</b>", section_style),
        ],
        [
            Paragraph(
                f"<b>{order.get('full_name') or 'Customer'}</b><br/>"
                f"Email: {order.get('email', '')}<br/>"
                f"Phone: {order.get('phone') or 'N/A'}<br/>"
                f"Address: {order.get('address') or ''}<br/>"
                f"{order.get('city') or ''}, {order.get('state') or ''} - {order.get('pincode') or ''}",
                cell_style,
            ),
            Paragraph(
                f"Order ID: #{order_id}<br/>"
                f"Status: <b>{str(order.get('status', 'Pending')).upper()}</b><br/>"
                f"Payment: {str(order.get('payment_method', 'N/A')).replace('_', ' ').title()}<br/>"
                f"Placed: {str(order.get('created_at', ''))[:19]}",
                cell_style,
            ),
        ],
    ]
    info_table = Table(customer_info, colWidths=[280, 250])
    info_table.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
    ]))
    story.append(info_table)
    story.append(Spacer(1, 20))

    # Items Table
    table_header = [
        Paragraph("<b>Item & Description</b>", cell_bold),
        Paragraph("<b>Qty</b>", cell_bold),
        Paragraph("<b>Unit Price</b>", cell_bold),
        Paragraph("<b>Total Amount</b>", cell_bold),
    ]
    table_data = [table_header]

    computed_subtotal = 0.0
    for it in items:
        qty = it.get("quantity", 1)
        u_price = it.get("unit_price", 0.0)
        line_total = qty * u_price
        computed_subtotal += line_total
        table_data.append([
            Paragraph(str(it.get("name", "Product")), cell_style),
            Paragraph(str(qty), cell_style),
            Paragraph(f"INR {u_price:,.2f}", cell_style),
            Paragraph(f"INR {line_total:,.2f}", cell_style),
        ])

    order_total = float(order.get("total") or computed_subtotal)
    table_data.append([
        Paragraph("<b>Total Due:</b>", cell_bold),
        "",
        "",
        Paragraph(f"<b>INR {order_total:,.2f}</b>", cell_bold),
    ])

    items_table = Table(table_data, colWidths=[250, 60, 110, 110])
    items_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1e293b")),
        ("ALIGN", (1, 0), (-1, -1), "RIGHT"),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("BOTTOMPADDING", (0, 0), (-1, 0), 8),
        ("TOPPADDING", (0, 0), (-1, 0), 8),
        ("GRID", (0, 0), (-1, -2), 0.5, colors.HexColor("#e2e8f0")),
        ("LINEBELOW", (0, -1), (-1, -1), 1.5, colors.HexColor("#1e293b")),
        ("TOPPADDING", (0, -1), (-1, -1), 10),
        ("BOTTOMPADDING", (0, -1), (-1, -1), 10),
        ("SPAN", (0, -1), (2, -1)),
    ]))
    story.append(items_table)
    story.append(Spacer(1, 30))

    # Footer note
    footer_text = (
        "Thank you for shopping with ShopZone! This is a system-generated electronic invoice "
        "and does not require a physical signature. For any support inquiries, contact support@shopzone.com."
    )
    story.append(Paragraph(footer_text, subtitle_style))

    _safe_update_state(
        self,
        state="PROGRESS",
        meta={
            "current": 85,
            "total": 100,
            "percent": 85,
            "message": "Writing invoice file to safe storage...",
            "status": "PROGRESS",
        },
    )

    doc.build(story)
    logger.info("Invoice generated successfully at: %s", file_path)

    # Sync invoice across workspaces if present
    for alt_base in [
        Path("C:/Users/Dell/Downloads/day19/backend/generated_invoices"),
        Path("C:/Users/Dell/Downloads/day9-fastapi/backend/generated_invoices"),
    ]:
        try:
            if alt_base.resolve() != file_path.parent.resolve() and alt_base.parent.exists():
                alt_base.mkdir(parents=True, exist_ok=True)
                shutil.copy2(file_path, alt_base / filename)
        except Exception as sync_err:
            logger.warning("Could not sync invoice to %s: %s", alt_base, sync_err)

    return {
        "status": "SUCCESS",
        "percent": 100,
        "order_id": order_id,
        "filename": filename,
        "file_size": os.path.getsize(file_path),
        "download_url": f"/orders/{order_id}/invoice/download",
        "message": f"Invoice for order #{order_id} generated successfully.",
    }


@celery_app.task(name="tasks.bulk_import_products_csv_task", bind=True)
def bulk_import_products_csv_task(self, file_path: str, user_email: str) -> dict[str, Any]:
    """Bulk import products from CSV into PostgreSQL database."""
    logger.info("Starting CSV product import from: %s", file_path)
    csv_path = Path(file_path)

    if not csv_path.exists():
        raise FileNotFoundError(f"Uploaded CSV file not found: {file_path}")

    _safe_update_state(
        self,
        state="PROGRESS",
        meta={
            "current": 0,
            "total": 100,
            "percent": 5,
            "message": "Reading CSV file structure...",
            "imported": 0,
            "failed": 0,
            "errors": [],
            "status": "PROGRESS",
        },
    )

    rows: List[Dict[str, str]] = []
    with open(csv_path, mode="r", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        if not reader.fieldnames:
            raise ValueError("CSV file is empty or missing header row")
        
        normalized_headers = {h.strip().lower(): h for h in reader.fieldnames if h}
        if "name" not in normalized_headers or "price" not in normalized_headers:
            raise ValueError("CSV must contain at least 'name' and 'price' columns")

        for row in reader:
            rows.append(row)

    total_rows = len(rows)
    if total_rows == 0:
        return {
            "status": "SUCCESS",
            "percent": 100,
            "imported_count": 0,
            "failed_count": 0,
            "total_rows": 0,
            "errors": [],
            "message": "CSV file contained 0 data rows.",
        }

    imported_count = 0
    failed_count = 0
    errors: List[Dict[str, Any]] = []
    valid_products: List[Dict[str, Any]] = []

    for idx, row in enumerate(rows, start=2):
        row_clean = {k.strip().lower(): (v.strip() if v else "") for k, v in row.items() if k}
        name = row_clean.get("name", "")
        price_str = row_clean.get("price", "")
        category = row_clean.get("category", "") or "General"
        image = row_clean.get("image", "") or "https://images.unsplash.com/photo-1523275335684-37898b6baf30?w=500"
        description = row_clean.get("description", "") or f"High quality {category}: {name}"
        stock_str = row_clean.get("stock", "50")

        if not name:
            failed_count += 1
            errors.append({"row": idx, "reason": "Missing product name"})
            continue

        try:
            price = float(price_str)
            if price <= 0:
                raise ValueError("Price must be greater than 0")
        except Exception:
            failed_count += 1
            errors.append({"row": idx, "name": name, "reason": f"Invalid price '{price_str}' (must be positive number)"})
            continue

        try:
            stock = int(stock_str) if stock_str else 50
            if stock < 0:
                raise ValueError("Stock cannot be negative")
        except Exception:
            failed_count += 1
            errors.append({"row": idx, "name": name, "reason": f"Invalid stock '{stock_str}' (must be non-negative integer)"})
            continue

        valid_products.append({
            "name": name,
            "price": price,
            "category": category,
            "image": image,
            "description": description,
            "stock": stock,
        })

        if idx % 10 == 0 or idx == total_rows + 1:
            progress_pct = int(((idx - 1) / total_rows) * 60) + 10
            _safe_update_state(
                self,
                state="PROGRESS",
                meta={
                    "current": idx - 1,
                    "total": total_rows,
                    "percent": min(progress_pct, 70),
                    "message": f"Validating row {idx - 1} of {total_rows}...",
                    "imported": len(valid_products),
                    "failed": failed_count,
                    "errors": errors[:10],
                    "status": "PROGRESS",
                },
            )

    _safe_update_state(
        self,
        state="PROGRESS",
        meta={
            "current": total_rows,
            "total": total_rows,
            "percent": 80,
            "message": f"Inserting {len(valid_products)} valid products into PostgreSQL database...",
            "imported": len(valid_products),
            "failed": failed_count,
            "errors": errors[:10],
            "status": "PROGRESS",
        },
    )

    with database_connection() as conn:
        for p in valid_products:
            existing = conn.execute(
                "SELECT id FROM products WHERE LOWER(name) = LOWER(%s)",
                (p["name"],),
            ).fetchone()

            if existing:
                conn.execute(
                    """
                    UPDATE products
                    SET price = %s, category = %s, image = %s, description = %s, stock = %s
                    WHERE id = %s
                    """,
                    (p["price"], p["category"], p["image"], p["description"], p["stock"], existing["id"]),
                )
            else:
                conn.execute(
                    """
                    INSERT INTO products (name, price, category, image, description, stock)
                    VALUES (%s, %s, %s, %s, %s, %s)
                    """,
                    (p["name"], p["price"], p["category"], p["image"], p["description"], p["stock"]),
                )
            imported_count += 1

    try:
        if csv_path.exists():
            csv_path.unlink()
    except Exception as cleanup_err:
        logger.warning("Could not delete temporary import file %s: %s", csv_path, cleanup_err)

    return {
        "status": "SUCCESS",
        "percent": 100,
        "imported_count": imported_count,
        "failed_count": failed_count,
        "total_rows": total_rows,
        "errors": errors,
        "message": f"CSV import completed: {imported_count} imported/updated, {failed_count} failed.",
    }
