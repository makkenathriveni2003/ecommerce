def test_create_order_and_history(client, shopper_token):
    order_payload = {
        "items": [{"product_id": 1, "quantity": 2}],
        "full_name": "Test Customer",
        "email": "shopper@example.com",
        "phone": "+91 9876543210",
        "address": "123 Test Street",
        "city": "Hyderabad",
        "state": "Telangana",
        "pincode": "500001",
        "payment_method": "card",
    }

    create_resp = client.post(
        "/orders",
        json=order_payload,
        headers={"Authorization": f"Bearer {shopper_token}"},
    )
    assert create_resp.status_code == 200
    created = create_resp.json()
    assert created["success"] is True
    order_id = created["order"]["id"]
    assert order_id > 0

    # Retrieve shopper order history
    history_resp = client.get(
        "/orders",
        headers={"Authorization": f"Bearer {shopper_token}"},
    )
    assert history_resp.status_code == 200
    orders = history_resp.json()
    assert any(o["id"] == order_id for o in orders)


def test_admin_update_order_status(client, shopper_token, admin_token):
    # First create an order
    order_payload = {
        "items": [{"product_id": 1, "quantity": 1}],
        "full_name": "Test Shopper",
        "email": "shopper@example.com",
        "phone": "9876543210",
        "address": "456 Avenue",
        "city": "Bengaluru",
        "state": "Karnataka",
        "pincode": "560001",
        "payment_method": "upi",
    }
    create_resp = client.post(
        "/orders",
        json=order_payload,
        headers={"Authorization": f"Bearer {shopper_token}"},
    )
    order_id = create_resp.json()["order"]["id"]

    # Admin updates order status to shipped
    update_resp = client.patch(
        f"/admin/orders/{order_id}/status",
        json={"status": "shipped"},
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert update_resp.status_code == 200
    res = update_resp.json()
    assert res["success"] is True
    assert res["order"]["status"] == "shipped"
