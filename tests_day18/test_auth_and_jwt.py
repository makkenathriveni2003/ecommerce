from auth import (
    hash_password,
    verify_password,
    create_access_token,
    read_access_token,
)


def test_password_hashing():
    pw = "Secret@Pass123"
    hashed = hash_password(pw)
    assert verify_password(pw, hashed) is True
    assert verify_password("WrongPassword", hashed) is False


def test_jwt_token_flow():
    email = "shopper@example.com"
    token = create_access_token(email)
    assert isinstance(token, str)

    extracted_email = read_access_token(token)
    assert extracted_email == email


def test_login_and_protected_me_endpoint(client):
    response = client.post(
        "/auth/login",
        json={"email": "shopper@example.com", "password": "Shopper@12345"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    token = data["token"]
    assert token

    # Access protected /auth/me
    me_resp = client.get(
        "/auth/me",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert me_resp.status_code == 200
    user_data = me_resp.json()
    assert user_data["email"] == "shopper@example.com"
    assert user_data["role"] == "shopper"


def test_unauthorized_access(client):
    # No token
    res1 = client.get("/auth/me")
    assert res1.status_code == 401

    # Invalid token
    res2 = client.get(
        "/auth/me",
        headers={"Authorization": "Bearer invalid.fake.token"},
    )
    assert res2.status_code == 401


def test_role_enforcement(client, shopper_token, admin_token):
    # Shopper cannot access admin orders
    res1 = client.get(
        "/admin/orders",
        headers={"Authorization": f"Bearer {shopper_token}"},
    )
    assert res1.status_code == 403

    # Admin can access admin orders
    res2 = client.get(
        "/admin/orders",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert res2.status_code == 200
