"""
ShopZone Day 25 Capstone - Master Static Deliverables Validator.
Verifies all Capstone deliverables, Gunicorn configuration, database pooling settings,
Docker resource constraints, backup & recovery scripts, documentation, and CI/CD workflows.
"""

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
DAY25_DIR = REPO_ROOT / "day25"
DOCS_DIR = DAY25_DIR / "docs"
SCRIPTS_DIR = DAY25_DIR / "scripts"
LOADTESTS_DIR = DAY25_DIR / "loadtests"

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
    print("=" * 72)
    print("      SHOPZONE DAY 25 CAPSTONE - MASTER DELIVERABLES VALIDATOR")
    print("=" * 72)

    # 1. Day 25 Core Configuration Deliverables
    check("Day 25 README exists", (DAY25_DIR / "README.md").exists())
    check("Day 25 .env.example exists", (DAY25_DIR / ".env.example").exists())
    check("Day 25 gunicorn_conf.py exists", (DAY25_DIR / "gunicorn_conf.py").exists())
    check("Day 25 docker-compose.prod.yml exists", (DAY25_DIR / "docker-compose.prod.yml").exists())
    check("Day 25 nginx.conf exists", (DAY25_DIR / "nginx.conf").exists())
    check("Root gunicorn_conf.py exists", (REPO_ROOT / "gunicorn_conf.py").exists())

    # 2. Day 25 Technical Documentation (10 Essential Deep Dives)
    docs = [
        "load-testing-bottlenecks.md",
        "database-connection-pooling.md",
        "production-server-gunicorn.md",
        "docker-resource-management.md",
        "postgres-backup-recovery.md",
        "final-deployment-cicd.md",
        "monitoring-error-tracking.md",
        "architectural-decisions.md",
        "peer-demo-script.md",
        "code-review-checklist.md",
    ]
    for doc in docs:
        check(f"Capstone Doc: {doc}", (DOCS_DIR / doc).exists())

    # 3. Load Testing Deliverables
    check("Locustfile exists", (LOADTESTS_DIR / "locustfile.py").exists())
    check("Load Test Scenarios doc exists", (LOADTESTS_DIR / "test_scenarios.md").exists())
    check("Load Test Benchmark CSV exists", (LOADTESTS_DIR / "locust_report_stats.csv").exists())
    check("Root locustfile_capstone.py exists", (REPO_ROOT / "loadtests" / "locustfile_capstone.py").exists())

    # 4. Capstone Automation & Disaster Recovery Scripts
    check("run_load_test.py exists", (SCRIPTS_DIR / "run_load_test.py").exists())
    check("backup_postgres.py exists", (SCRIPTS_DIR / "backup_postgres.py").exists())
    check("backup_postgres.sh exists", (SCRIPTS_DIR / "backup_postgres.sh").exists())
    check("restore_postgres.py exists", (SCRIPTS_DIR / "restore_postgres.py").exists())
    check("restore_postgres.sh exists", (SCRIPTS_DIR / "restore_postgres.sh").exists())
    check("test_backup_recovery.py exists", (SCRIPTS_DIR / "test_backup_recovery.py").exists())
    check("validate_docker_resources.py exists", (SCRIPTS_DIR / "validate_docker_resources.py").exists())
    check("run_day25_tests.py exists", (SCRIPTS_DIR / "run_day25_tests.py").exists())

    # 5. Core Codebase Enhancements
    config_py = (REPO_ROOT / "backend" / "app" / "core" / "config.py").read_text(encoding="utf-8")
    check("DB_POOL_SIZE configured in config.py", "DB_POOL_SIZE" in config_py)
    check("DB_MAX_OVERFLOW configured in config.py", "DB_MAX_OVERFLOW" in config_py)

    session_py = (REPO_ROOT / "backend" / "app" / "db" / "session.py").read_text(encoding="utf-8")
    check("get_db_pool_status defined in session.py", "def get_db_pool_status" in session_py)

    main_py = (REPO_ROOT / "backend" / "app" / "main.py").read_text(encoding="utf-8")
    check("connection_pool in /health components", '"connection_pool"' in main_py)

    dockerfile_backend = (REPO_ROOT / "Dockerfile.backend").read_text(encoding="utf-8")
    check("Dockerfile.backend copies gunicorn_conf.py", "gunicorn_conf.py" in dockerfile_backend)
    check("Dockerfile.backend runs Gunicorn", "gunicorn" in dockerfile_backend)

    requirements_txt = (REPO_ROOT / "backend" / "requirements.txt").read_text(encoding="utf-8")
    check("gunicorn listed in requirements.txt", "gunicorn" in requirements_txt)

    # 6. CI/CD Workflows
    check("CI workflow exists", (REPO_ROOT / ".github" / "workflows" / "ci.yml").exists())
    check("Capstone CI/CD workflow exists", (REPO_ROOT / ".github" / "workflows" / "capstone-ci-cd.yml").exists())

    print("\n" + "=" * 72)
    print(f"VALIDATION SUMMARY: {PASSED_CHECKS} / {TOTAL_CHECKS} CHECKS PASSED")
    print("=" * 72)

    return 0 if (PASSED_CHECKS == TOTAL_CHECKS) else 1


if __name__ == "__main__":
    sys.exit(main())
