import os
import sys
from pathlib import Path
import pytest
from fastapi.testclient import TestClient

# Ensure backend folder is in python path
backend_path = Path(__file__).resolve().parent.parent / "backend"
if str(backend_path) not in sys.path:
    sys.path.insert(0, str(backend_path))

from main import app
from database import initialize_database
from auth import create_access_token


@pytest.fixture(scope="session", autouse=True)
def setup_test_db():
    initialize_database()


@pytest.fixture
def client():
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture
def admin_token():
    return create_access_token("admin@example.com")


@pytest.fixture
def shopper_token():
    return create_access_token("shopper@example.com")
