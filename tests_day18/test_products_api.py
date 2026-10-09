def test_get_products_catalog(client):
    response = client.get("/products")
    assert response.status_code == 200
    products = response.json()
    assert isinstance(products, list)
    assert len(products) > 0
    assert "name" in products[0]
    assert "price" in products[0]


def test_search_products(client):
    # Search by category or name
    response = client.get("/products?search=Laptop")
    assert response.status_code == 200
    results = response.json()
    assert len(results) > 0
    assert any("laptop" in p["name"].lower() for p in results)


def test_get_single_product(client):
    response = client.get("/products/1")
    assert response.status_code == 200
    product = response.json()
    assert product["id"] == 1
    assert "name" in product


def test_get_nonexistent_product(client):
    response = client.get("/products/999999")
    assert response.status_code == 404
