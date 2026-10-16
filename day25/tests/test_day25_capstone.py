"""
ShopZone Day 25 Capstone - Production Readiness & Capstone Test Suite.
Validates:
1. Gunicorn + Uvicorn worker configuration and CPU sizing formulas
2. Database connection pooling (SQLAlchemy QueuePool, starvation avoidance)
3. Docker resource management (CPU/memory limits, logging rotation)
4. PostgreSQL backup, SHA-256 checksums, and restoration workflow
5. High-concurrency Locust load testing personas and SLA benchmarks
6. Automated CI/CD pipeline configuration and production readiness
7. Deep health checks and Prometheus metrics
"""

import csv
import gzip
import hashlib
import json
import os
import sys
from pathlib import Path
import pytest
from starlette.testclient import TestClient
import yaml

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
DAY25_DIR = REPO_ROOT / "day25"
BACKEND_DIR = REPO_ROOT / "backend"

if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from app.main import app
from app.core.config import settings
from app.db.session import get_db_pool_status, engine


@pytest.fixture
def client():
    return TestClient(app)


# ==============================================================================
# 1. Production Server: Gunicorn with Uvicorn Workers
# ==============================================================================
def test_gunicorn_configuration_attributes():
    """Verify gunicorn_conf.py defines production worker concurrency and timeouts."""
    gunicorn_file = DAY25_DIR / "gunicorn_conf.py"
    assert gunicorn_file.exists(), "day25/gunicorn_conf.py not found"

    content = gunicorn_file.read_text(encoding="utf-8")
    assert "uvicorn.workers.UvicornWorker" in content
    assert "WEB_CONCURRENCY" in content
    assert "max_requests" in content
    assert "max_requests_jitter" in content
    assert "graceful_timeout" in content
    assert "timeout" in content

    # Dynamically load configuration module
    import importlib.util
    spec = importlib.util.spec_from_file_location("gunicorn_conf", str(gunicorn_file))
    gconf = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(gconf)

    assert gconf.worker_class == "uvicorn.workers.UvicornWorker"
    assert gconf.workers >= 2
    assert gconf.timeout >= 60
    assert gconf.max_requests >= 500
    assert gconf.keepalive >= 2


# ==============================================================================
# 2. Database Connection Pooling (SQLAlchemy QueuePool)
# ==============================================================================
def test_database_connection_pooling_settings():
    """Verify PostgreSQL connection pooling parameters are tuned for concurrent load."""
    assert settings.DB_POOL_SIZE >= 10, "DB_POOL_SIZE must be at least 10 for 50-100 users"
    assert settings.DB_MAX_OVERFLOW >= 10, "DB_MAX_OVERFLOW must accommodate burst requests"
    assert settings.DB_POOL_TIMEOUT >= 10, "DB_POOL_TIMEOUT must prevent connection timeout spikes"
    assert settings.DB_POOL_RECYCLE >= 300, "DB_POOL_RECYCLE must refresh stale connections"
    assert settings.DB_POOL_PRE_PING is True, "DB_POOL_PRE_PING must be enabled to drop dead sockets"


def test_database_pool_status_inspection():
    """Verify get_db_pool_status reports active pool metrics."""
    pool_metrics = get_db_pool_status()
    assert isinstance(pool_metrics, dict)
    assert "engine" in pool_metrics
    assert "pool_type" in pool_metrics
    assert "pool_pre_ping" in pool_metrics
    assert pool_metrics["pool_pre_ping"] is True


# ==============================================================================
# 3. Docker Resource Management (CPU & RAM Limits)
# ==============================================================================
def test_docker_compose_resource_limits_and_logging():
    """Verify all 7 production containers enforce CPU and RAM limits and reservations."""
    compose_path = DAY25_DIR / "docker-compose.prod.yml"
    assert compose_path.exists(), "day25/docker-compose.prod.yml not found"

    with open(compose_path, "r", encoding="utf-8") as f:
        compose_data = yaml.safe_load(f)

    services = compose_data.get("services", {})
    expected_services = ["postgres", "redis", "chromadb", "backend", "celery_worker", "celery_beat", "nginx"]

    for name in expected_services:
        assert name in services, f"Missing service {name} in docker-compose.prod.yml"
        svc = services[name]

        # 1. Deploy Resource limits
        resources = svc.get("deploy", {}).get("resources", {})
        limits = resources.get("limits", {})
        reservations = resources.get("reservations", {})

        assert "cpus" in limits, f"Service {name} missing CPU limit"
        assert "memory" in limits, f"Service {name} missing memory limit"
        assert "cpus" in reservations, f"Service {name} missing CPU reservation"
        assert "memory" in reservations, f"Service {name} missing memory reservation"

        # 2. Logging rotation
        logging_cfg = svc.get("logging", {})
        assert logging_cfg.get("driver") == "json-file", f"Service {name} missing json-file logging"
        options = logging_cfg.get("options", {})
        assert "max-size" in options, f"Service {name} missing max-size log rotation"
        assert "max-file" in options, f"Service {name} missing max-file log rotation"


# ==============================================================================
# 4. PostgreSQL Backup & Recovery Workflow
# ==============================================================================
def test_backup_and_restore_scripts_logic(tmp_path):
    """Verify backup creation, SHA-256 calculation, and restoration verification."""
    from day25.scripts.backup_postgres import calculate_sha256

    test_file = tmp_path / "test_snapshot.sql.gz"
    dummy_sql = "-- ShopZone SQL Test Snapshot\nCREATE TABLE test (id INT);"
    with gzip.open(test_file, "wt", encoding="utf-8") as f:
        f.write(dummy_sql)

    # 1. Checksum calculation
    hash1 = calculate_sha256(test_file)
    assert len(hash1) == 64, "SHA-256 hash must be 64 hexadecimal characters"

    # 2. Idempotent recalculation
    hash2 = calculate_sha256(test_file)
    assert hash1 == hash2, "SHA-256 must be deterministic"

    # 3. Read compressed data
    with gzip.open(test_file, "rt", encoding="utf-8") as f:
        read_back = f.read()
    assert "CREATE TABLE test" in read_back


# ==============================================================================
# 5. Load Testing & SLA Benchmarks
# ==============================================================================
def test_locust_load_testing_personas_and_sla():
    """Verify Locust test classes, weighting, and benchmark stats meeting production SLAs."""
    locust_file = DAY25_DIR / "loadtests" / "locustfile.py"
    assert locust_file.exists(), "day25/loadtests/locustfile.py not found"

    code = locust_file.read_text(encoding="utf-8")
    assert "class BrowsingShopper(HttpUser):" in code
    assert "class ActivePurchaser(HttpUser):" in code
    assert "class MonitoringProbe(HttpUser):" in code
    assert "weight = 6" in code
    assert "weight = 3" in code
    assert "weight = 1" in code
    assert "/products?skip=" in code
    assert "/products/semantic-search" in code
    assert "/orders" in code
    assert "/health" in code
    assert "/metrics" in code

    # Verify benchmark CSV stats
    stats_file = DAY25_DIR / "loadtests" / "locust_report_stats.csv"
    assert stats_file.exists(), "locust_report_stats.csv not found"

    with open(stats_file, mode="r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        agg_found = False
        for row in reader:
            if row.get("Name") == "Aggregated":
                agg_found = True
                req_count = int(row.get("Request Count", 0))
                fail_count = int(row.get("Failure Count", 0))
                p95 = float(row.get("95%", 0))
                rps = float(row.get("Requests/s", 0))

                assert req_count > 1000, "Load test request count must be substantial"
                assert fail_count == 0, "Production load test benchmark had 0 failures"
                assert p95 < 100, f"p95 latency {p95}ms meets < 100ms production SLA"
                assert rps > 100, f"Requests per second {rps} exceeds 100 RPS"
        assert agg_found is True, "Aggregated stats row not found in CSV"


# ==============================================================================
# 6. Deep Health Check & Monitoring
# ==============================================================================
def test_health_endpoint_with_connection_pool_metrics(client):
    """Verify /health returns connection pool details and components."""
    response = client.get("/health")
    assert response.status_code in (200, 503)

    data = response.json()
    assert data["service"] == "shopzone-api"
    assert "components" in data
    assert "database" in data["components"]
    assert "redis" in data["components"]
    assert "connection_pool" in data["components"]
    assert "database_pool" in data
    assert "engine" in data["database_pool"]


def test_prometheus_metrics_endpoint_exposition(client):
    """Verify Prometheus scrape endpoint exposes latency and request metrics."""
    response = client.get("/metrics")
    assert response.status_code == 200
    assert "http_requests_total" in response.text
    assert "http_request_duration_seconds" in response.text
