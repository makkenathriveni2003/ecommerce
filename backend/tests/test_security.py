from app.core.security import create_access_token
from app.db.database import database_connection


def test_unauthorized_access_to_protected_endpoints(client):
    # No Authorization header
    res1 = client.get("/auth/me")
    assert res1.status_code == 401

    res2 = client.get("/orders")
    assert res2.status_code == 401

    res3 = client.get("/admin/orders")
    assert res3.status_code == 401


def test_forbidden_access_by_non_admin_role(client, shopper_token):
    headers = {"Authorization": f"Bearer {shopper_token}"}

    # Admin product creation
    res1 = client.post(
        "/admin/products",
        headers=headers,
        json={"name": "Hacked", "price": 10.0, "category": "General", "image": "http://img.png"},
    )
    assert res1.status_code == 403

    # Admin orders list
    res2 = client.get("/admin/orders", headers=headers)
    assert res2.status_code == 403

    # Admin update order status
    res3 = client.patch(
        "/admin/orders/1/status",
        headers=headers,
        json={"status": "delivered"},
    )
    assert res3.status_code == 403


def test_broken_object_level_authorization_idor(client):
    """OWASP API1: Verify user A cannot generate or download invoice for user B's order."""
    with database_connection() as conn:
        orders = conn.execute("SELECT id, user_id, email FROM orders WHERE user_id IS NOT NULL LIMIT 2").fetchall()
    
    if len(orders) >= 1:
        target_order = orders[0]
        # Register a distinct attacker shopper
        client.post(
            "/auth/register",
            json={"name": "Attacker User", "email": "attacker@example.com", "password": "Password123!"},
        )
        attacker_token = create_access_token("attacker@example.com", role="shopper")
        headers = {"Authorization": f"Bearer {attacker_token}"}

        # Attempt to trigger invoice generation on another user's order
        res = client.post(f"/orders/{target_order['id']}/invoice", headers=headers)
        if target_order["email"] != "attacker@example.com":
            assert res.status_code == 403
            assert "permission" in res.json()["detail"].lower()

        # Attempt to download invoice of another user's order
        dl_res = client.get(f"/orders/{target_order['id']}/invoice/download", headers=headers)
        if target_order["email"] != "attacker@example.com":
            assert dl_res.status_code in (403, 404)


def test_input_validation_and_safe_error_responses(client, admin_token):
    headers = {"Authorization": f"Bearer {admin_token}"}

    # Negative price
    res1 = client.post(
        "/admin/products",
        headers=headers,
        json={"name": "Bad Price", "price": -50.0, "category": "Test", "image": "http://img.png"},
    )
    assert res1.status_code == 422

    # Empty name
    res2 = client.post(
        "/admin/products",
        headers=headers,
        json={"name": "", "price": 100.0, "category": "Test", "image": "http://img.png"},
    )
    assert res2.status_code == 422


def test_security_headers_present(client):
    res = client.get("/")
    assert res.status_code == 200
    assert res.headers.get("X-Content-Type-Options") == "nosniff"
    assert res.headers.get("X-Frame-Options") == "DENY"
    assert "Content-Security-Policy" in res.headers
