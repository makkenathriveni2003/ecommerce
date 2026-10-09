"""
ShopZone FastAPI Application Entrypoint
Initializes and re-exports the modular application from app.main.
"""
from pathlib import Path
import sys

# Ensure backend root is in sys.path
backend_dir = str(Path(__file__).resolve().parent)
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

from app.main import app
from app.core.config import settings
from app.core.security import require_authenticated_user, require_admin, create_access_token
from app.db.database import database_connection, initialize_database
from app.tasks.celery_tasks import sample_background_job_task, generate_invoice_pdf_task, bulk_import_products_csv_task

from app.services.order_service import (
    get_sqlalchemy_orders_optimized,
    attach_order_items as _attach_order_items,
    order_items_for_orders as _order_items,
)
from app.db.database import _detect_engine

__all__ = [
    "app",
    "settings",
    "require_authenticated_user",
    "require_admin",
    "create_access_token",
    "database_connection",
    "initialize_database",
    "sample_background_job_task",
    "generate_invoice_pdf_task",
    "bulk_import_products_csv_task",
    "get_sqlalchemy_orders_optimized",
    "_attach_order_items",
    "_order_items",
    "_detect_engine",
]

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="127.0.0.1", port=8000, reload=True)
