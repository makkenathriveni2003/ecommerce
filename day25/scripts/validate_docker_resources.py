"""
ShopZone Day 25 Capstone - Docker Resource Management Validator.
Inspects production Docker Compose definitions to guarantee CPU and memory
limits/reservations and logging driver rotation are configured on all services.
"""

import sys
from pathlib import Path
import yaml

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
COMPOSE_FILE = REPO_ROOT / "day25" / "docker-compose.prod.yml"

REQUIRED_SERVICES = [
    "postgres",
    "redis",
    "chromadb",
    "backend",
    "celery_worker",
    "celery_beat",
    "nginx",
]


def validate_resources():
    print("=" * 72)
    print("      DOCKER RESOURCE MANAGEMENT & CONTAINER STABILITY VALIDATOR")
    print("=" * 72)

    if not COMPOSE_FILE.exists():
        print(f"[FAIL] Compose file not found: {COMPOSE_FILE}")
        return 1

    with open(COMPOSE_FILE, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)

    services = data.get("services", {})
    all_passed = True

    for name in REQUIRED_SERVICES:
        svc = services.get(name)
        if not svc:
            print(f"[FAIL] Missing service '{name}' in docker-compose.prod.yml")
            all_passed = False
            continue

        deploy = svc.get("deploy", {})
        resources = deploy.get("resources", {})
        limits = resources.get("limits", {})
        reservations = resources.get("reservations", {})

        cpu_limit = limits.get("cpus")
        mem_limit = limits.get("memory")
        cpu_res = reservations.get("cpus")
        mem_res = reservations.get("memory")

        # Logging check
        logging_cfg = svc.get("logging", {})
        log_driver = logging_cfg.get("driver")
        log_opts = logging_cfg.get("options", {})
        max_size = log_opts.get("max-size")

        has_limits = bool(cpu_limit and mem_limit)
        has_reservations = bool(cpu_res and mem_res)
        has_logging = bool(log_driver == "json-file" and max_size)

        if has_limits and has_reservations and has_logging:
            print(
                f"[PASS] {name:15} | CPU: {cpu_res}->{cpu_limit} | "
                f"RAM: {mem_res}->{mem_limit} | Log: {log_driver} ({max_size})"
            )
        else:
            print(
                f"[FAIL] {name:15} | Limits: {has_limits} | "
                f"Reservations: {has_reservations} | Logging: {has_logging}"
            )
            all_passed = False

    if all_passed:
        print("\n>>> ALL 7 PRODUCTION CONTAINERS PASS RESOURCE CONSTRAINTS (100%) <<<")
        return 0
    else:
        print("\n>>> DOCKER RESOURCE VALIDATION FAILED <<<")
        return 1


if __name__ == "__main__":
    sys.exit(validate_resources())
