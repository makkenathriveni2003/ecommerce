import uuid
import pytest
from app.core.security import hash_password, verify_password, create_access_token, read_access_token


def test_password_hashing():
    pwd = "SecurePassword123!"
    hashed = hash_password(pwd)
    assert verify_password(pwd, hashed) is True
    assert verify_password("WrongPassword!", hashed) is False
    assert not hashed.startswith("SecurePassword")


def test_jwt_generation_and_reading():
    email = "testuser@example.com"
    token = create_access_token(email, role="shopper")
    decoded_email = read_access_token(token)
    assert decoded_email == email

    with pytest.raises(ValueError):
        read_access_token(token + "tampered")


def test_register_and_login_flow(client):
    unique_email = f"user_{uuid.uuid4().hex[:8]}@example.com"
    password = "StrongPassword123!"

    # 1. Register
    reg_res = client.post(
        "/auth/register",
        json={"name": "Test Shopper", "email": unique_email, "password": password},
    )
    assert reg_res.status_code == 200
    assert reg_res.json()["success"] is True

    # 2. Duplicate registration
    dup_res = client.post(
        "/auth/register",
        json={"name": "Duplicate Shopper", "email": unique_email, "password": password},
    )
    assert dup_res.status_code == 409

    # 3. Login
    login_res = client.post(
        "/auth/login",
        json={"email": unique_email, "password": password},
    )
    assert login_res.status_code == 200
    login_data = login_res.json()
    assert login_data["success"] is True
    assert "token" in login_data
    token = login_data["token"]

    # 4. Access /auth/me
    me_res = client.get("/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert me_res.status_code == 200
    assert me_res.json()["email"] == unique_email


def test_invalid_login(client):
    res = client.post(
        "/auth/login",
        json={"email": "nonexistent@example.com", "password": "WrongPassword123!"},
    )
    assert res.status_code == 401
    assert "Invalid email or password" in res.json()["detail"]
