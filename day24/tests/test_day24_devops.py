"""
ShopZone Day 24 - DevOps, Observability, and AWS Stack Test Suite.
Verifies structured logging, correlation IDs, PII redaction, health checks,
Prometheus metrics, Sentry integration, Nginx configuration, and Vercel settings.
"""

import json
import logging
from pathlib import Path
import pytest
from starlette.testclient import TestClient
import yaml

from app.main import app
from app.core.config import settings
from app.core.logging_config import StructuredJsonFormatter, sanitize_text, sanitize_data
from app.core.sentry import init_sentry, before_send_filter

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
DAY24_DIR = REPO_ROOT / "day24"


@pytest.fixture
def client():
    return TestClient(app)


def test_structured_logging_json_format_and_pii_scrubbing():
    """Verify StructuredJsonFormatter outputs valid JSON and redacts credentials."""
    formatter = StructuredJsonFormatter(service_name="shopzone-api")
    
    # 1. Test basic record formatting
    record = logging.LogRecord(
        name="test.module",
        level=logging.INFO,
        pathname="test.py",
        lineno=10,
        msg="User authenticated successfully with Bearer eyJhbGciOiJIUzI1NiJ9.test and password=SuperSecretPassword123!",
        args=(),
        exc_info=None,
    )
    formatted = formatter.format(record)
    data = json.loads(formatted)
    
    assert data["level"] == "INFO"
    assert data["service"] == "shopzone-api"
    assert data["module"] == "test.module"
    assert "timestamp" in data
    
    # 2. Verify PII & token redaction
    assert "SuperSecretPassword123" not in data["message"]
    assert "[FILTERED]" in data["message"]
    assert "Bearer [FILTERED]" in data["message"]

    # 3. Test data dictionary sanitization
    sensitive_dict = {
        "username": "thriveni",
        "password": "mypassword",
        "token": "secret_jwt_token",
        "nested": {"api_key": "secret_api_key", "public_info": "safe"},
    }
    clean_dict = sanitize_data(sensitive_dict)
    assert clean_dict["username"] == "thriveni"
    assert clean_dict["password"] == "[FILTERED]"
    assert clean_dict["token"] == "[FILTERED]"
    assert clean_dict["nested"]["api_key"] == "[FILTERED]"
    assert clean_dict["nested"]["public_info"] == "safe"


def test_request_id_correlation_middleware(client):
    """Verify X-Request-ID header is propagated or generated on every response."""
    # 1. Custom incoming request ID
    custom_id = "test-corr-id-12345"
    response = client.get("/health", headers={"X-Request-ID": custom_id})
    assert response.headers.get("X-Request-ID") == custom_id

    # 2. Auto-generated request ID when header is absent
    response_auto = client.get("/")
    gen_id = response_auto.headers.get("X-Request-ID")
    assert gen_id is not None
    assert len(gen_id) >= 16


def test_health_endpoint_response_structure_and_codes(client):
    """Verify /health returns structured JSON with component status and no secrets."""
    response = client.get("/health")
    assert response.status_code in (200, 503)
    
    data = response.json()
    assert "status" in data
    assert data["service"] == "shopzone-api"
    assert "version" in data
    assert "components" in data
    assert "database" in data["components"]
    assert "redis" in data["components"]
    assert data["components"]["database"] in ("healthy", "unhealthy")
    
    # Ensure no internal credentials, URLs, or hostnames leak
    raw_text = response.text.lower()
    assert "password" not in raw_text
    assert "postgres://" not in raw_text
    assert "redis://" not in raw_text


def test_prometheus_metrics_endpoint(client):
    """Verify /metrics returns standard Prometheus exposition metrics."""
    response = client.get("/metrics")
    assert response.status_code == 200
    assert "text/plain" in response.headers.get("content-type", "")
    
    content = response.text
    assert "http_requests_total" in content
    assert "http_request_duration_seconds" in content
    assert "shopzone_app_info" in content


def test_sentry_optional_initialization_and_before_send():
    """Verify Sentry handles missing DSN gracefully and scrubs PII in events."""
    # Empty DSN must return False without throwing exceptions
    assert init_sentry(dsn="") is False

    # Verify before_send_filter scrubs headers
    test_event = {
        "request": {
            "headers": {
                "Authorization": "Bearer sensitive_token",
                "Cookie": "session=secret_session",
                "User-Agent": "Mozilla/5.0",
            },
            "data": {
                "username": "user1",
                "password": "plain_password",
            },
        }
    }
    filtered = before_send_filter(test_event, {})
    headers = filtered["request"]["headers"]
    assert headers["Authorization"] == "[FILTERED]"
    assert headers["Cookie"] == "[FILTERED]"
    assert headers["User-Agent"] == "Mozilla/5.0"
    assert filtered["request"]["data"]["password"] == "[FILTERED]"


def test_nginx_configuration_validity():
    """Verify day24/nginx.conf has required proxy headers, buffering, and WebSocket directives."""
    conf_path = DAY24_DIR / "nginx.conf"
    assert conf_path.exists()
    
    content = conf_path.read_text(encoding="utf-8")
    assert "upstream backend_api" in content
    assert "server backend:8000" in content
    assert "location /health" in content
    assert "location /metrics" in content
    assert "location /api/" in content
    assert "location /ai/" in content
    assert "proxy_buffering off" in content
    assert "location /ws" in content
    assert "proxy_set_header Upgrade $http_upgrade" in content
    assert "location /.well-known/acme-challenge/" in content


def test_vercel_configuration_validity():
    """Verify frontend/vercel.json is valid JSON with SPA history rewrites."""
    vercel_path = REPO_ROOT / "frontend" / "vercel.json"
    assert vercel_path.exists()
    
    with open(vercel_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    
    assert data.get("framework") == "vite"
    assert data.get("buildCommand") == "npm run build"
    assert data.get("outputDirectory") == "dist"
    
    rewrites = data.get("rewrites", [])
    has_spa_rewrite = any(r.get("source") == "/(.*)" and r.get("destination") == "/index.html" for r in rewrites)
    assert has_spa_rewrite, "vercel.json must rewrite all paths to /index.html"


def test_prometheus_scrape_config_validity():
    """Verify day24/prometheus.yml is valid YAML and targets backend:8000."""
    prom_path = DAY24_DIR / "prometheus.yml"
    assert prom_path.exists()
    
    with open(prom_path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)
    
    assert "scrape_configs" in data
    configs = data["scrape_configs"]
    backend_job = next((c for c in configs if c.get("job_name") == "shopzone-backend"), None)
    assert backend_job is not None
    assert backend_job.get("metrics_path") == "/metrics"
    targets = backend_job["static_configs"][0]["targets"]
    assert "backend:8000" in targets


def test_docker_compose_prod_validity():
    """Verify day24/docker-compose.prod.yml defines required production services."""
    compose_path = DAY24_DIR / "docker-compose.prod.yml"
    assert compose_path.exists()
    
    with open(compose_path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)
    
    services = data.get("services", {})
    required = ["postgres", "redis", "backend", "celery_worker", "nginx"]
    for svc in required:
        assert svc in services, f"Production docker-compose must define service '{svc}'"
    
    # Verify Nginx maps ports 80 and 443
    nginx_ports = services["nginx"].get("ports", [])
    assert any("80:80" in p for p in nginx_ports)
    assert any("443:443" in p for p in nginx_ports)


def test_day24_documentation_completeness():
    """Verify all 11 required Day 24 technical guides exist in day24/docs."""
    docs_dir = DAY24_DIR / "docs"
    required_docs = [
        "aws-ec2-setup.md",
        "nginx-https-certbot.md",
        "vercel-deployment.md",
        "sentry-logging-guide.md",
        "health-monitoring-uptimerobot.md",
        "aws-iam-least-privilege.md",
        "s3-static-hosting.md",
        "load-balancing-autoscaling.md",
        "cloudwatch-monitoring.md",
        "deployment-troubleshooting.md",
        "verification-checklist.md",
    ]
    for doc in required_docs:
        doc_path = docs_dir / doc
        assert doc_path.exists(), f"Day 24 documentation '{doc}' must exist"
        assert doc_path.stat().st_size > 500, f"Document '{doc}' should contain detailed content"
