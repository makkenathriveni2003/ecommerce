import io
import time
from auth import create_access_token
from tasks import bulk_import_products_csv_task
from database import database_connection

def test_csv_import_file_validation(client):
    """Rejects non-csv file upload."""
    token = create_access_token("admin@example.com")
    file_content = b"This is not a CSV"
    response = client.post(
        "/admin/products/import-csv",
        headers={"Authorization": f"Bearer {token}"},
        files={"file": ("invalid.txt", io.BytesIO(file_content), "text/plain")},
    )
    assert response.status_code == 400
    assert "csv" in response.json()["detail"].lower()


def test_csv_import_endpoint_flow(client, tmp_path):
    """Test queuing CSV import through API endpoint."""
    token = create_access_token("admin@example.com")
    csv_data = (
        "name,price,category,image,description,stock\n"
        "Mechanical Keyboard,4500.0,Electronics,https://images.unsplash.com/photo-1587829741301-dc798b83add3?w=500,RGB Gaming Keyboard,35\n"
        "Ergonomic Mouse,1800.0,Accessories,https://images.unsplash.com/photo-1527864550417-7fd91fc51a46?w=500,Wireless Mouse,50\n"
    ).encode("utf-8")

    response = client.post(
        "/admin/products/import-csv",
        headers={"Authorization": f"Bearer {token}"},
        files={"file": ("products_import.csv", io.BytesIO(csv_data), "text/csv")},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert "task_id" in data
    assert data["status"] == "PENDING"
    task_id = data["task_id"]

    # Poll status
    status_resp = client.get(f"/tasks/{task_id}/status")
    assert status_resp.status_code == 200
    status_data = status_resp.json()
    assert status_data["task_id"] == task_id


def test_bulk_import_products_csv_task_execution(tmp_path):
    """Test actual Celery task processing with row validation, error handling, and DB upsert."""
    csv_file = tmp_path / "test_import.csv"
    csv_content = (
        "name,price,category,image,description,stock\n"
        "Ultra Wide Monitor,32000.0,Electronics,https://images.unsplash.com/photo-1527443224154-c4a3942d3acf?w=500,34 inch curved monitor,15\n"
        ",500.0,Electronics,,,20\n"  # Invalid: Missing name
        "Broken Price Item,-100.0,Accessories,,,10\n"  # Invalid: Negative price
        "Bad Stock Item,250.0,Accessories,,,abc\n"  # Invalid: Non-numeric stock
        "Noise Cancelling Earbuds,8999.0,Electronics,https://images.unsplash.com/photo-1590658268037-6bf12165a8df?w=500,Active Noise Cancellation,40\n"
    )
    csv_file.write_text(csv_content, encoding="utf-8")

    result = bulk_import_products_csv_task(str(csv_file), "admin@example.com")
    assert result["status"] == "SUCCESS"
    assert result["imported_count"] == 2
    assert result["failed_count"] == 3
    assert len(result["errors"]) == 3

    # Verify products are present in database
    with database_connection() as conn:
        row = conn.execute(
            "SELECT name, price, stock FROM products WHERE name = %s",
            ("Ultra Wide Monitor",),
        ).fetchone()
        assert row is not None
        assert float(row["price"]) == 32000.0
        assert int(row["stock"]) == 15
