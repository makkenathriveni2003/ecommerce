import time
import uuid
import logging
from typing import Any, List
from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile

from ...core.config import settings
from ...core.security import require_admin, require_authenticated_user
from ...schemas.schemas import BulkImportResponse, ProductData
from ...services.product_service import (
    create_product,
    get_product,
    get_products,
    get_similar_products,
    semantic_search_products,
)
from ...tasks.celery_tasks import bulk_import_products_csv_task

logger = logging.getLogger("shopzone_products_router")
router = APIRouter(prefix="/products", tags=["Products"])


@router.get("/semantic-search")
def semantic_search(
    q: str = Query(..., min_length=1, description="Semantic product search query"),
    limit: int = Query(default=20, ge=1, le=50),
) -> list[dict[str, object]]:
    """
    Day 22 Semantic Search: Uses ChromaDB vector embeddings to match user shopping intent.
    Retrieves records matching contextual similarity and falls back gracefully.
    """
    return semantic_search_products(query=q, limit=limit)


@router.get("/search")
def search_products(
    q: str = Query(..., min_length=1, description="Product search query"),
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=50, ge=1, le=100),
    semantic: bool = Query(default=False, description="Enable AI embedding-based semantic search"),
) -> list[dict[str, object]]:
    if semantic:
        return semantic_search_products(query=q, limit=limit)
    return get_products(skip=skip, limit=limit, search=q)


@router.get("")
@router.get("/")
def list_products(
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=100, ge=1, le=100),
    search: str | None = Query(default=None),
) -> list[dict[str, object]]:
    return get_products(skip=skip, limit=limit, search=search)


@router.get("/{product_id}")
def retrieve_product(product_id: int) -> dict[str, object]:
    return get_product(product_id)


@router.get("/{product_id}/similar")
def retrieve_similar_products(
    product_id: int,
    limit: int = Query(default=4, ge=1, le=12),
) -> list[dict[str, object]]:
    return get_similar_products(product_id=product_id, limit=limit)


@router.post("", dependencies=[Depends(require_admin)])
def add_product(product: ProductData) -> dict[str, object]:
    return create_product(product)


@router.post("/import-csv", response_model=BulkImportResponse)
async def import_products_csv(
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
