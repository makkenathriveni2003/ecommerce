import io
import uuid


def test_get_products_catalog(client):
    res = client.get("/products")
    assert res.status_code == 200
    products = res.json()
    assert isinstance(products, list)
    assert len(products) > 0
    first = products[0]
    assert "id" in first
    assert "name" in first
    assert "price" in first
    assert "category" in first


def test_search_products(client):
    # Search for Laptop
    res = client.get("/products/search?q=Laptop")
    assert res.status_code == 200
    results = res.json()
    assert isinstance(results, list)
    assert any("laptop" in p["name"].lower() for p in results)

    # Fuzzy search for typo
    res_fuzzy = client.get("/products/search?q=laptp")
    assert res_fuzzy.status_code == 200
    fuzzy_results = res_fuzzy.json()
    assert isinstance(fuzzy_results, list)


def test_single_product_crud(client, admin_token):
    headers = {"Authorization": f"Bearer {admin_token}"}
    unique_name = f"Test Product {uuid.uuid4().hex[:6]}"

    # Create
    create_res = client.post(
        "/admin/products",
        headers=headers,
        json={
            "name": unique_name,
            "price": 1299.99,
            "category": "Testing",
            "image": "https://example.com/item.png",
            "description": "A product for automated test suite",
            "stock": 25,
        },
    )
    assert create_res.status_code == 200
    created = create_res.json()
    product_id = created["id"]
    assert created["name"] == unique_name

    # Retrieve
    get_res = client.get(f"/products/{product_id}")
    assert get_res.status_code == 200
    assert get_res.json()["id"] == product_id

    # Update
    update_res = client.put(
        f"/admin/products/{product_id}",
        headers=headers,
        json={
            "name": f"{unique_name} Updated",
            "price": 1499.99,
            "category": "Testing",
            "image": "https://example.com/item2.png",
            "description": "Updated description",
            "stock": 30,
        },
    )
    assert update_res.status_code == 200
    assert update_res.json()["name"] == f"{unique_name} Updated"

    # Delete
    del_res = client.delete(f"/admin/products/{product_id}", headers=headers)
    assert del_res.status_code == 200
    assert del_res.json()["success"] is True

    # Confirm 404
    get_after = client.get(f"/products/{product_id}")
    assert get_after.status_code == 404


def test_bulk_csv_import_file_validation(client, admin_token):
    headers = {"Authorization": f"Bearer {admin_token}"}
    non_csv = b"plain text data"
    res = client.post(
        "/admin/products/import-csv",
        headers=headers,
        files={"file": ("test.txt", io.BytesIO(non_csv), "text/plain")},
    )
    assert res.status_code == 400
