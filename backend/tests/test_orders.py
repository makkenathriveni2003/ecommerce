import time
from app.db.database import database_connection


def test_create_order_and_history_flow(client, shopper_token):
    headers = {"Authorization": f"Bearer {shopper_token}"}

    # Fetch valid product ID
    with database_connection() as conn:
        prod = conn.execute("SELECT id, price FROM products LIMIT 1").fetchone()
    assert prod is not None

    product_id = prod["id"]
    order_payload = {
        "items": [{"product_id": product_id, "quantity": 2}],
        "full_name": "Jane Shopper",
        "email": "shopper@example.com",
        "phone": "9876543210",
        "address": "123 Shopping Lane",
        "city": "Metropolis",
        "state": "State",
        "pincode": "560001",
        "payment_method": "card",
    }

    create_res = client.post("/orders", headers=headers, json=order_payload)
    assert create_res.status_code == 200
    data = create_res.json()
    assert data["success"] is True
    order = data["order"]
    assert order["status"] == "pending"
    assert len(order["items"]) == 1
    assert order["items"][0]["quantity"] == 2

    # Get history
    hist_res = client.get("/orders", headers=headers)
    assert hist_res.status_code == 200
    orders_list = hist_res.json()
    assert isinstance(orders_list, list)
    assert any(o["id"] == order["id"] for o in orders_list)


def test_create_order_nonexistent_product(client, shopper_token):
    headers = {"Authorization": f"Bearer {shopper_token}"}
    order_payload = {
        "items": [{"product_id": 999999, "quantity": 1}],
        "full_name": "Jane Shopper",
        "email": "shopper@example.com",
        "phone": "9876543210",
        "address": "123 Shopping Lane",
        "city": "Metropolis",
        "state": "State",
        "pincode": "560001",
        "payment_method": "upi",
    }
    res = client.post("/orders", headers=headers, json=order_payload)
    assert res.status_code == 404
    assert "not found" in res.json()["detail"].lower()


def test_optimized_orders_endpoints(client, shopper_token, admin_token):
    # Customer optimized endpoint
    c_res = client.get("/orders/optimized", headers={"Authorization": f"Bearer {shopper_token}"})
    assert c_res.status_code == 200
    assert isinstance(c_res.json(), list)

    # Admin optimized endpoint
    a_res = client.get("/admin/orders/optimized", headers={"Authorization": f"Bearer {admin_token}"})
    assert a_res.status_code == 200
    assert isinstance(a_res.json(), list)


def test_order_status_update_by_admin(client, admin_token):
    headers = {"Authorization": f"Bearer {admin_token}"}
    with database_connection() as conn:
        order = conn.execute("SELECT id FROM orders ORDER BY id DESC LIMIT 1").fetchone()
    assert order is not None

    update_res = client.patch(
        f"/admin/orders/{order['id']}/status",
        headers=headers,
        json={"status": "shipped"},
    )
    assert update_res.status_code == 200
    assert update_res.json()["order"]["status"] == "shipped"
