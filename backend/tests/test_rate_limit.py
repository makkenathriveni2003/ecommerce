import uuid
from starlette.requests import Request
from app.core.rate_limit import get_client_ip, limiter


def test_client_ip_extraction():
    # Direct remote address mock
    scope = {"type": "http", "headers": [(b"x-forwarded-for", b"203.0.113.195, 70.41.3.18")]}
    req = Request(scope)
    ip = get_client_ip(req)
    assert ip == "203.0.113.195"

    # Real IP header
    scope2 = {"type": "http", "headers": [(b"x-real-ip", b"198.51.100.4")]}
    req2 = Request(scope2)
    assert get_client_ip(req2) == "198.51.100.4"


def test_rate_limit_trigger_and_response(client):
    """Trigger login attempts from a unique simulated IP until rate limit responds with 429."""
    simulated_ip = f"192.168.10.{uuid.uuid4().int % 250 + 1}"
    headers = {"X-Forwarded-For": simulated_ip}

    status_codes = []
    # Login limit is 5/minute by default
    for _ in range(8):
        res = client.post(
            "/auth/login",
            headers=headers,
            json={"email": "nonexistent@example.com", "password": "WrongPassword123!"},
        )
        status_codes.append(res.status_code)
        if res.status_code == 429:
            data = res.json()
            assert "Rate limit exceeded" in data.get("error", "") or "Rate limit exceeded" in data.get("detail", "")
            assert "Retry-After" in res.headers
            break

    assert 429 in status_codes, f"Expected 429 in status codes: {status_codes}"
