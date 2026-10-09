import sys
from pathlib import Path
import pytest
from fastapi.testclient import TestClient

backend_dir = Path(__file__).resolve().parent.parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

from app.main import app
from app.db.database import initialize_database
from app.core.security import create_access_token


@pytest.fixture(scope="session", autouse=True)
def setup_test_db():
    initialize_database()


@pytest.fixture
def client():
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture
def admin_token():
    return create_access_token("admin@example.com", role="admin")


@pytest.fixture
def shopper_token():
    return create_access_token("shopper@example.com", role="shopper")
