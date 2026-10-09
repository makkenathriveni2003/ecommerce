import json
import time
import uuid
from app.db.database import database_connection


def test_gzip_compression_verification(client):
    """Verify GZip response compression for responses >= minimum_size (1000 bytes)."""
    # 1. Request product catalog without gzip
    res_plain = client.get("/products")
    assert res_plain.status_code == 200
    plain_content = res_plain.content
    plain_size = len(plain_content)

    # 2. Request product catalog with gzip encoding
    res_gzip = client.get("/products", headers={"Accept-Encoding": "gzip"})
    assert res_gzip.status_code == 200

    # In starlette/testclient, Content-Encoding is returned as 'gzip' when compressed
    encoding = res_gzip.headers.get("content-encoding")
    if plain_size >= 1000:
        assert encoding == "gzip" or res_gzip.headers.get("x-gzip") is not None or "gzip" in str(res_gzip.headers)
    
    # Verify content integrity
    data_plain = res_plain.json()
    data_gzip = res_gzip.json()
    assert data_plain == data_gzip
    assert len(data_gzip) > 0


def test_small_response_not_compressed(client):
    """Verify small response (< 1000 bytes) is not compressed."""
    res = client.get("/", headers={"Accept-Encoding": "gzip"})
    assert res.status_code == 200
    # Root message is ~50 bytes, smaller than 1000-byte threshold
    assert res.headers.get("Content-Encoding") != "gzip"


def test_end_to_end_user_journey(client):
    """
    Complete end-to-end user journey:
    1. Register user
    2. Login user and acquire JWT
    3. Search and select product
    4. Place order
    5. Trigger PDF invoice generation via Celery
    6. Verify invoice status polling
    7. Download invoice PDF
    """
    user_email = f"journey_{uuid.uuid4().hex[:6]}@example.com"
    password = "SuperPassword123!"

    # 1. Register
    reg_resp = client.post(
        "/auth/register",
        json={"name": "End To End User", "email": user_email, "password": password},
    )
    assert reg_resp.status_code == 200

    # 2. Login
    login_resp = client.post(
        "/auth/login",
        json={"email": user_email, "password": password},
    )
    assert login_resp.status_code == 200
    token = login_resp.json()["token"]
    auth_header = {"Authorization": f"Bearer {token}"}

    # 3. Product Catalog & Search
    products_resp = client.get("/products/search?q=Mobile")
    assert products_resp.status_code == 200
    products = products_resp.json()
    assert len(products) > 0
    selected_product = products[0]

    # 4. Create Order
    order_payload = {
        "items": [{"product_id": selected_product["id"], "quantity": 1}],
        "full_name": "End To End User",
        "email": user_email,
        "phone": "9988776655",
        "address": "456 Market Boulevard",
        "city": "Bengaluru",
        "state": "Karnataka",
        "pincode": "560001",
        "payment_method": "upi",
    }
    order_resp = client.post("/orders", headers=auth_header, json=order_payload)
    assert order_resp.status_code == 200
    order_id = order_resp.json()["order"]["id"]

    # 5. Generate PDF Invoice
    invoice_resp = client.post(f"/orders/{order_id}/invoice", headers=auth_header)
    assert invoice_resp.status_code == 200
    task_id = invoice_resp.json()["task_id"]

    # 6. Poll Task Status
    task_success = False
    for _ in range(30):
        status_resp = client.get(f"/tasks/{task_id}/status")
        assert status_resp.status_code == 200
        sdata = status_resp.json()
        if sdata["status"] == "SUCCESS":
            task_success = True
            break
        time.sleep(0.2)

    assert task_success is True, "Invoice generation task timed out"

    # 7. Download Invoice PDF
    dl_resp = client.get(f"/orders/{order_id}/invoice/download", headers=auth_header)
    assert dl_resp.status_code == 200
    assert dl_resp.headers["content-type"] == "application/pdf"
    assert len(dl_resp.content) > 500
