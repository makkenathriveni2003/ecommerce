"""
Backward-compatibility adapter for tasks module.
Re-exports from app.tasks.celery_tasks.
"""
from app.tasks.celery_tasks import (
    sample_background_job_task,
    generate_invoice_pdf_task,
    bulk_import_products_csv_task,
    INVOICE_DIR,
)

__all__ = [
    "sample_background_job_task",
    "generate_invoice_pdf_task",
    "bulk_import_products_csv_task",
    "INVOICE_DIR",
]
