"""
ShopZone Day 24 - DevOps & AWS Focus Static Validator.
Verifies all Day 24 deliverables, configuration files, Nginx reverse proxy directives,
Docker Compose definitions, Vercel SPA configuration, and documentation completeness.
"""

import sys
from pathlib import Path

def find_repo_root() -> Path:
    curr = Path(__file__).resolve().parent
    for _ in range(5):
        if (curr / "backend").exists() and (curr / "frontend").exists():
            return curr
        curr = curr.parent
    return Path.cwd()

REPO_ROOT = find_repo_root()
DAY24_DIR = REPO_ROOT / "day24"
DOCS_DIR = DAY24_DIR / "docs"

TOTAL_CHECKS = 0
PASSED_CHECKS = 0

def check(name: str, condition: bool, details: str = "") -> bool:
    global TOTAL_CHECKS, PASSED_CHECKS
    TOTAL_CHECKS += 1
    if condition:
        PASSED_CHECKS += 1
        print(f"[PASS] {name}")
        return True
    else:
        print(f"[FAIL] {name} - {details}")
        return False


def main() -> int:
    print("=" * 70)
    print("       SHOPZONE DAY 24 DEVOPS & AWS STACK STATIC VALIDATOR")
    print("=" * 70)

    # 1. Day 24 Deliverable Files
    check("Day 24 README exists", (DAY24_DIR / "README.md").exists())
    check("Day 24 .env.example exists", (DAY24_DIR / ".env.example").exists())
    check("Day 24 nginx.conf exists", (DAY24_DIR / "nginx.conf").exists())
    check("Day 24 docker-compose.prod.yml exists", (DAY24_DIR / "docker-compose.prod.yml").exists())
    check("Day 24 prometheus.yml exists", (DAY24_DIR / "prometheus.yml").exists())

    # 2. Day 24 Technical Documentation
    doc_files = [
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
    for doc in doc_files:
        check(f"Doc: {doc}", (DOCS_DIR / doc).exists())

    # 3. Source Code Integrations
    check("Backend logging_config.py exists", (REPO_ROOT / "backend" / "app" / "core" / "logging_config.py").exists())
    check("Backend metrics.py exists", (REPO_ROOT / "backend" / "app" / "core" / "metrics.py").exists())
    check("Backend sentry.py exists", (REPO_ROOT / "backend" / "app" / "core" / "sentry.py").exists())
    check("Backend request_logging.py middleware exists", (REPO_ROOT / "backend" / "app" / "middleware" / "request_logging.py").exists())
    check("Frontend sentry.ts utility exists", (REPO_ROOT / "frontend" / "src" / "utils" / "sentry.ts").exists())
    check("Frontend vercel.json exists", (REPO_ROOT / "frontend" / "vercel.json").exists())

    # 4. Nginx Reverse Proxy Directives
    nginx_content = (DAY24_DIR / "nginx.conf").read_text(encoding="utf-8")
    check("Nginx defines upstream backend_api", "upstream backend_api" in nginx_content)
    check("Nginx has /health location", "location /health" in nginx_content)
    check("Nginx has /metrics location", "location /metrics" in nginx_content)
    check("Nginx has /api/ location", "location /api/" in nginx_content)
    check("Nginx has /ai/ location with buffering disabled", "location /ai/" in nginx_content and "proxy_buffering off" in nginx_content)
    check("Nginx has /ws location with WebSocket upgrade", "location /ws" in nginx_content and "Upgrade" in nginx_content)
    check("Nginx has Certbot acme-challenge location", "/.well-known/acme-challenge/" in nginx_content)

    # 5. Vercel Configuration
    vercel_content = (REPO_ROOT / "frontend" / "vercel.json").read_text(encoding="utf-8")
    check("Vercel framework is vite", '"framework": "vite"' in vercel_content)
    check("Vercel rewrites to /index.html", '"destination": "/index.html"' in vercel_content)

    # 6. Production Compose Stack
    compose_content = (DAY24_DIR / "docker-compose.prod.yml").read_text(encoding="utf-8")
    check("Docker Compose has backend service", "backend:" in compose_content)
    check("Docker Compose has celery_worker service", "celery_worker:" in compose_content)
    check("Docker Compose has postgres service", "postgres:" in compose_content)
    check("Docker Compose has redis service", "redis:" in compose_content)
    check("Docker Compose has nginx service", "nginx:" in compose_content)

    # 7. Secrets & Git Ignore
    gitignore_content = (REPO_ROOT / ".gitignore").read_text(encoding="utf-8")
    check("Gitignore protects .pem files", "*.pem" in gitignore_content)
    check("Gitignore protects .key files", "*.key" in gitignore_content)
    check("Gitignore protects day24/.env", "day24/.env" in gitignore_content)

    # 8. Backend Dependencies
    reqs_content = (REPO_ROOT / "backend" / "requirements.txt").read_text(encoding="utf-8")
    check("Backend requirements has sentry-sdk", "sentry-sdk" in reqs_content)
    check("Backend requirements has prometheus-client", "prometheus-client" in reqs_content)

    print("=" * 70)
    print(f"Results: {PASSED_CHECKS} / {TOTAL_CHECKS} checks passed.")
    print("=" * 70)

    return 0 if PASSED_CHECKS == TOTAL_CHECKS else 1


if __name__ == "__main__":
    sys.exit(main())
