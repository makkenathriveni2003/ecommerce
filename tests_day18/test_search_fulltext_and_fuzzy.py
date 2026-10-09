import pytest

def test_full_text_search_endpoint(client):
    """Test full-text product search via /products/search?q=electronics."""
    response = client.get("/products/search?q=electronics")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) > 0
    names = [p["name"].lower() for p in data]
    assert any("laptop" in name or "mobile" in name or "iphone" in name for name in names)


def test_fuzzy_search_typo_laptop(client):
    """Verify typo-tolerant fuzzy search: 'laptpo' resolves to 'Laptop' via pg_trgm."""
    response = client.get("/products/search?q=laptpo")
    assert response.status_code == 200
    data = response.json()
    assert len(data) > 0
    top_result = data[0]
    assert "laptop" in top_result["name"].lower()


def test_fuzzy_search_typo_iphone(client):
    """Verify typo-tolerant fuzzy search: 'iphnoe' resolves to iPhone product via pg_trgm."""
    response = client.get("/products/search?q=iphnoe")
    assert response.status_code == 200
    data = response.json()
    assert len(data) > 0
    top_result = data[0]
    assert "iphone" in top_result["name"].lower()


def test_search_via_products_query_param(client):
    """Verify /products?search=... also routes through the combined full-text + fuzzy search."""
    response = client.get("/products?search=laptpo")
    assert response.status_code == 200
    data = response.json()
    assert len(data) > 0
    assert "laptop" in data[0]["name"].lower()
