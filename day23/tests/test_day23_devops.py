"""
Day 23 DevOps & AWS Focus - Comprehensive Test Suite
Validates Docker multi-stage configurations, Docker Compose orchestration,
networking, persistent volumes, GitHub Actions CI/CD workflows,
and product color variant matching logic.
"""
import os
import re
from pathlib import Path
import pytest
import yaml

REPO_ROOT = Path(__file__).resolve().parent.parent.parent


def test_dockerfile_backend_multistage():
    """Verify backend Dockerfile implements multi-stage builds, non-root user, and healthchecks."""
    dockerfile_path = REPO_ROOT / "Dockerfile.backend"
    assert dockerfile_path.exists(), "Dockerfile.backend must exist at repo root"

    content = dockerfile_path.read_text(encoding="utf-8")
    assert "AS builder" in content, "Backend Dockerfile must have a builder stage"
    assert "AS runner" in content, "Backend Dockerfile must have a runner stage"
    assert "useradd" in content or "adduser" in content, "Must create an unprivileged user"
    assert "USER appuser" in content or "USER " in content, "Must switch to non-root user"
    assert "HEALTHCHECK" in content, "Must specify a HEALTHCHECK for container orchestrators"
    assert "8000" in content, "Must expose backend port 8000"


def test_dockerfile_frontend_multistage():
    """Verify frontend Dockerfile uses multi-stage node builder and lean nginx runner."""
    dockerfile_path = REPO_ROOT / "Dockerfile.frontend"
    assert dockerfile_path.exists(), "Dockerfile.frontend must exist at repo root"

    content = dockerfile_path.read_text(encoding="utf-8")
    assert "node:" in content.lower(), "Frontend builder must use Node.js image"
    assert "AS builder" in content, "Frontend Dockerfile must have a builder stage"
    assert "nginx:" in content.lower(), "Frontend runner must use Nginx image"
    assert "COPY --from=builder" in content, "Must copy compiled static files from builder"
    assert "HEALTHCHECK" in content, "Must define container healthcheck"


def test_nginx_conf_reverse_proxy_and_gzip():
    """Verify nginx.conf provides gzip compression, security headers, and reverse proxy."""
    nginx_path = REPO_ROOT / "nginx.conf"
    assert nginx_path.exists(), "nginx.conf must exist at repo root"

    content = nginx_path.read_text(encoding="utf-8")
    assert "gzip on;" in content, "Gzip compression must be enabled"
    assert "proxy_pass http://backend:8000;" in content, "Must proxy /api/ to backend service"
    assert "proxy_buffering off;" in content, "Must disable buffering for SSE streaming"
    assert "Upgrade $http_upgrade;" in content, "Must support WebSocket upgrades"
    assert "X-Frame-Options" in content, "Must include security headers"


def test_docker_compose_services():
    """Verify docker-compose.yml configures all required services and health dependencies."""
    compose_path = REPO_ROOT / "docker-compose.yml"
    assert compose_path.exists(), "docker-compose.yml must exist at repo root"

    with open(compose_path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)

    services = data.get("services", {})
    required_services = [
        "backend",
        "frontend",
        "postgres",
        "redis",
        "celery_worker",
        "celery_beat",
        "chromadb",
    ]

    for req in required_services:
        assert req in services, f"docker-compose.yml must define service '{req}'"

    # Verify backend dependencies
    backend = services["backend"]
    assert "postgres" in backend.get("depends_on", {}), "Backend must depend on postgres"
    assert "redis" in backend.get("depends_on", {}), "Backend must depend on redis"

    # Verify celery worker dependencies
    celery = services["celery_worker"]
    assert "redis" in celery.get("depends_on", {}), "Celery worker must depend on redis"


def test_docker_networking_and_volumes():
    """Verify docker-compose defines custom bridge network and named persistent volumes."""
    compose_path = REPO_ROOT / "docker-compose.yml"
    with open(compose_path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)

    networks = data.get("networks", {})
    assert "shopzone-network" in networks or "thriveni-network" in networks, "Must configure custom bridge network"

    volumes = data.get("volumes", {})
    required_volumes = [
        "postgres_data",
        "redis_data",
        "chroma_data",
        "app_logs",
        "app_uploads",
    ]
    for v in required_volumes:
        assert v in volumes, f"Must define persistent named volume '{v}'"


def test_github_actions_ci_workflow():
    """Verify .github/workflows/ci.yml configures automated testing and quality gates."""
    ci_path = REPO_ROOT / ".github" / "workflows" / "ci.yml"
    assert ci_path.exists(), ".github/workflows/ci.yml must exist"

    with open(ci_path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)

    jobs = data.get("jobs", {})
    assert "lint-and-typecheck" in jobs, "CI workflow must have lint-and-typecheck job"
    assert "backend-tests" in jobs, "CI workflow must have backend-tests job"
    assert "frontend-tests" in jobs, "CI workflow must have frontend-tests job"
    assert "docker-validate" in jobs, "CI workflow must have docker-validate job"

    # Verify service containers in backend-tests
    backend_job = jobs["backend-tests"]
    services = backend_job.get("services", {})
    assert "postgres" in services, "CI must run PostgreSQL service container for testing"
    assert "redis" in services, "CI must run Redis service container for testing"


def test_github_actions_docker_build_push():
    """Verify .github/workflows/docker-build-push.yml configures multi-arch and caching."""
    bp_path = REPO_ROOT / ".github" / "workflows" / "docker-build-push.yml"
    assert bp_path.exists(), ".github/workflows/docker-build-push.yml must exist"

    content = bp_path.read_text(encoding="utf-8")
    assert "docker/build-push-action" in content, "Must use official docker/build-push-action"
    assert "type=gha" in content, "Must use GitHub Actions layer cache"
    assert "platforms:" in content, "Must support multi-architecture builds"


def test_env_files_and_secrets_management():
    """Verify environment templates define complete variables without committing raw secrets."""
    docker_env = REPO_ROOT / ".env.docker"
    assert docker_env.exists(), ".env.docker must exist"
    content_docker = docker_env.read_text(encoding="utf-8")
    assert "DATABASE_URL" in content_docker
    assert "CELERY_BROKER_URL" in content_docker
    assert "REDIS_URL" in content_docker

    prod_env = REPO_ROOT / ".env.production.example"
    assert prod_env.exists(), ".env.production.example must exist"
    content_prod = prod_env.read_text(encoding="utf-8")
    assert "CHANGE_THIS" in content_prod or "${" in content_prod, "Production template must use placeholders"


def test_product_variants_color_consistency():
    """Verify dresses and jeans in productVariants.ts provide consistent matching color styles."""
    pv_path = REPO_ROOT / "frontend" / "src" / "utils" / "productVariants.ts"
    assert pv_path.exists(), "productVariants.ts must exist"
    content = pv_path.read_text(encoding="utf-8")

    # Verify bottomwear / jeans has indigo, washed black, and light washed blue
    assert "Classic Indigo Denim" in content
    assert "Midnight Washed Black" in content
    assert "Vintage Light Washed Blue" in content

    # Verify dresses has distinct sky blue, emerald green, and crimson red
    assert "Pastel Sky Blue" in content
    assert "Emerald Festive Green" in content
    assert "Ruby Crimson Red" in content
    assert "Blush Floral Rose" in content


def test_day23_folder_in_vscode():
    """Verify day23 folder is completely populated with all required DevOps artifacts."""
    day23_dir = REPO_ROOT / "day23"
    assert day23_dir.exists() and day23_dir.is_dir(), "day23 folder must exist in workspace"

    expected_files = [
        "Dockerfile.backend",
        "Dockerfile.frontend",
        "nginx.conf",
        "docker-compose.yml",
        "docker-compose.prod.yml",
        ".dockerignore",
        ".env.docker",
        ".env.production.example",
    ]
    for ef in expected_files:
        assert (day23_dir / ef).exists(), f"day23/{ef} must exist"

    assert (day23_dir / "github-workflows" / "ci.yml").exists()
    assert (day23_dir / "github-workflows" / "docker-build-push.yml").exists()
    assert (day23_dir / "github-workflows" / "branch-protection.yml").exists()
