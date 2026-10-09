import time
from pathlib import Path
from fastapi.testclient import TestClient
import pytest
from auth import create_access_token
from database import database_connection
from main import app
from tasks import INVOICE_DIR

client = TestClient(app)

def test_invoice_generation_flow():
    """Verify end-to-end PDF invoice generation through Celery and ReportLab."""
    # 1. Fetch an existing order and its user
    with database_connection() as conn:
        order = conn.execute(
            """
            SELECT o.id, o.user_id, o.email, o.total, u.role
            FROM orders o
            JOIN users u ON u.id = o.user_id
            LIMIT 1
            """
        ).fetchone()

    assert order is not None, "At least one order must exist in PostgreSQL"
    order_id = order["id"]
    user_email = order["email"]

    token = create_access_token(user_email)
    headers = {"Authorization": f"Bearer {token}"}

    # 2. Trigger invoice generation via API
    resp = client.post(f"/orders/{order_id}/invoice", headers=headers)
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert data["success"] is True
    assert "task_id" in data
    assert data["order_id"] == order_id
    task_id = data["task_id"]

    # 3. Poll task status through Celery and Redis
    terminal = False
    for _ in range(30):
        status_res = client.get(f"/tasks/{task_id}/status")
        assert status_res.status_code == 200
        sdata = status_res.json()
        if sdata["status"] == "SUCCESS":
            terminal = True
            assert sdata["percent"] == 100
            assert "filename" in sdata["result"]
            break
        elif sdata["status"] == "FAILURE":
            pytest.fail(f"Invoice generation failed: {sdata.get('error')}")
        time.sleep(0.3)

    assert terminal is True, "Invoice task did not reach SUCCESS within timeout"

    # 4. Verify PDF file on disk
    pdf_path = INVOICE_DIR / f"ShopZone_Invoice_{order_id}.pdf"
    assert pdf_path.exists(), f"PDF file not found at {pdf_path}"
    pdf_bytes = pdf_path.read_bytes()
    assert len(pdf_bytes) > 500, "PDF file is suspiciously small"
    assert pdf_bytes.startswith(b"%PDF-"), "File is not a valid PDF document"

    # 5. Verify download endpoint
    dl_resp = client.get(f"/orders/{order_id}/invoice/download", headers=headers)
    assert dl_resp.status_code == 200
    assert dl_resp.headers["content-type"] == "application/pdf"
    assert len(dl_resp.content) == len(pdf_bytes)
    assert dl_resp.content.startswith(b"%PDF-")

    # 6. Verify 404 for nonexistent order
    nonexistent_resp = client.post("/orders/999999/invoice", headers=headers)
    assert nonexistent_resp.status_code == 404
