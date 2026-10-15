"""
Day 23 DevOps & Docker Stack Validator
Performs static analysis and verification of Dockerfiles, docker-compose.yml,
nginx.conf, and GitHub Actions CI/CD workflows.
"""
from pathlib import Path
import sys
import yaml

def find_repo_root() -> Path:
    curr = Path(__file__).resolve().parent
    for _ in range(5):
        if (curr / "backend").exists() and (curr / "frontend").exists():
            return curr
        curr = curr.parent
    return Path.cwd()

REPO_ROOT = find_repo_root()


def check(name: str, condition: bool, detail: str = ""):
    status = "PASS" if condition else "FAIL"
    print(f"[{status}] {name} {f'({detail})' if detail else ''}")
    if not condition:
        return False
    return True


def validate_all():
    all_ok = True
    print("=" * 70)
    print("      DAY 23 DEVOPS / AWS CONTAINERIZATION & CI/CD VALIDATOR")
    print("=" * 70)

    # 1. Backend Dockerfile
    df_backend = REPO_ROOT / "Dockerfile.backend"
    all_ok &= check("Backend Dockerfile Exists", df_backend.exists(), str(df_backend))
    if df_backend.exists():
        c = df_backend.read_text(encoding="utf-8")
        all_ok &= check("Backend Multi-Stage (builder stage)", "AS builder" in c)
        all_ok &= check("Backend Multi-Stage (runner stage)", "AS runner" in c)
        all_ok &= check("Backend Non-Root User Created", "useradd" in c or "adduser" in c)
        all_ok &= check("Backend Non-Root User Switched", "USER appuser" in c or "USER 1001" in c or "USER thriveni" in c)
        all_ok &= check("Backend HEALTHCHECK Configured", "HEALTHCHECK" in c)
        all_ok &= check("Backend Port 8000 Exposed", "EXPOSE 8000" in c)

    # 2. Frontend Dockerfile
    df_frontend = REPO_ROOT / "Dockerfile.frontend"
    all_ok &= check("Frontend Dockerfile Exists", df_frontend.exists(), str(df_frontend))
    if df_frontend.exists():
        c = df_frontend.read_text(encoding="utf-8")
        all_ok &= check("Frontend Multi-Stage (Node builder)", "node:" in c.lower() and "AS builder" in c)
        all_ok &= check("Frontend Lean Nginx Runner", "nginx:" in c.lower() and "AS runner" in c)
        all_ok &= check("Frontend HEALTHCHECK Configured", "HEALTHCHECK" in c)

    # 3. Nginx Configuration
    nginx_f = REPO_ROOT / "nginx.conf"
    all_ok &= check("Nginx Configuration Exists", nginx_f.exists())
    if nginx_f.exists():
        c = nginx_f.read_text(encoding="utf-8")
        all_ok &= check("Nginx Gzip Compression Enabled", "gzip on;" in c)
        all_ok &= check("Nginx Reverse Proxy /api/ to backend:8000", "proxy_pass http://backend:8000;" in c)
        all_ok &= check("Nginx SSE Buffering Disabled", "proxy_buffering off;" in c)
        all_ok &= check("Nginx WebSocket Upgrade Header", "Upgrade $http_upgrade;" in c)

    # 4. Docker Compose
    dc_f = REPO_ROOT / "docker-compose.yml"
    all_ok &= check("docker-compose.yml Exists", dc_f.exists())
    if dc_f.exists():
        with open(dc_f, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)
        services = data.get("services", {})
        required = ["backend", "frontend", "postgres", "redis", "celery_worker", "celery_beat", "chromadb"]
        for s in required:
            all_ok &= check(f"Docker Compose Service: '{s}'", s in services)

        volumes = data.get("volumes", {})
        req_vols = ["postgres_data", "redis_data", "chroma_data", "app_logs", "app_uploads"]
        for v in req_vols:
            all_ok &= check(f"Persistent Volume: '{v}'", v in volumes)

        networks = data.get("networks", {})
        all_ok &= check("Custom Bridge Network Configured", "shopzone-network" in networks or "thriveni-network" in networks)

    # 5. GitHub Actions Workflows
    ci_f = REPO_ROOT / ".github" / "workflows" / "ci.yml"
    all_ok &= check("GitHub Actions CI Workflow Exists", ci_f.exists())
    if ci_f.exists():
        with open(ci_f, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)
        jobs = data.get("jobs", {})
        all_ok &= check("CI Job: lint-and-typecheck", "lint-and-typecheck" in jobs)
        all_ok &= check("CI Job: backend-tests with Postgres & Redis services", "backend-tests" in jobs)
        all_ok &= check("CI Job: frontend-tests (Vitest)", "frontend-tests" in jobs)
        all_ok &= check("CI Job: docker-validate", "docker-validate" in jobs)

    bp_f = REPO_ROOT / ".github" / "workflows" / "docker-build-push.yml"
    all_ok &= check("Docker Build & Push Workflow Exists", bp_f.exists())

    prot_f = REPO_ROOT / ".github" / "workflows" / "branch-protection.yml"
    all_ok &= check("Branch Protection Workflow Exists", prot_f.exists())

    # 6. Environment Configurations
    all_ok &= check(".env.docker Exists", (REPO_ROOT / ".env.docker").exists())
    all_ok &= check(".env.production.example Exists", (REPO_ROOT / ".env.production.example").exists())

    # 7. Day 23 VS Code Folder Integrity
    day23_dir = REPO_ROOT / "day23"
    all_ok &= check("Dedicated day23/ folder exists in VS Code", day23_dir.exists())

    print("=" * 70)
    if all_ok:
        print(">>> ALL 26 DEVOPS & DOCKER VALIDATION CHECKS PASSED (100%) <<<")
        return 0
    else:
        print(">>> SOME CHECKS FAILED! PLEASE REVIEW OUTPUT ABOVE <<<")
        return 1


if __name__ == "__main__":
    sys.exit(validate_all())
