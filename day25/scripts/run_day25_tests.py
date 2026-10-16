"""
ShopZone Day 25 Capstone - Complete Master Test & Validation Runner.
Executes static deliverable validation, Docker resource verification,
disaster recovery backup & restoration drills, and automated Pytest test suites.
"""

import subprocess
import sys
from pathlib import Path


def find_repo_root() -> Path:
    curr = Path(__file__).resolve().parent
    for _ in range(5):
        if (curr / "backend").exists() and (curr / "day25").exists():
            return curr
        curr = curr.parent
    return Path.cwd()


REPO_ROOT = find_repo_root()
DAY25_DIR = REPO_ROOT / "day25"
SCRIPTS_DIR = DAY25_DIR / "scripts"


def main():
    print("=" * 72)
    print("      RUNNING SHOPZONE DAY 25 CAPSTONE: MASTER VERIFICATION SUITE")
    print("=" * 72)

    # 1. Static Deliverables Validation
    print("\n--- 1. STATIC DELIVERABLES VALIDATION ---")
    val_script = SCRIPTS_DIR / "validate_day25_capstone.py"
    r1 = subprocess.run([sys.executable, str(val_script)])
    if r1.returncode != 0:
        print("[FAIL] Static deliverables validation failed.")
        return r1.returncode

    # 2. Docker Resource Management Validation
    print("\n--- 2. DOCKER RESOURCE MANAGEMENT VALIDATION ---")
    docker_val = SCRIPTS_DIR / "validate_docker_resources.py"
    r2 = subprocess.run([sys.executable, str(docker_val)])
    if r2.returncode != 0:
        print("[FAIL] Docker resource management validation failed.")
        return r2.returncode

    # 3. Database Backup & Disaster Recovery Drill
    print("\n--- 3. DATABASE BACKUP & RESTORATION DRILL ---")
    drill_script = SCRIPTS_DIR / "test_backup_recovery.py"
    r3 = subprocess.run([sys.executable, str(drill_script)])
    if r3.returncode != 0:
        print("[FAIL] Database backup and restoration drill failed.")
        return r3.returncode

    # 4. Day 25 Capstone Pytest Suite
    print("\n--- 4. DAY 25 CAPSTONE PYTEST SUITE ---")
    test_file = DAY25_DIR / "tests" / "test_day25_capstone.py"
    r4 = subprocess.run([
        sys.executable, "-m", "pytest",
        str(test_file),
        "-v"
    ])
    if r4.returncode != 0:
        print("[FAIL] Day 25 Capstone Pytest suite failed.")
        return r4.returncode

    # 5. Regression Check on Backend Tests
    print("\n--- 5. FULL BACKEND REGRESSION SUITE ---")
    r5 = subprocess.run([
        sys.executable, "-m", "pytest",
        str(REPO_ROOT / "backend" / "tests"),
        "-q"
    ])
    if r5.returncode != 0:
        print("[FAIL] Backend regression suite failed.")
        return r5.returncode

    print("\n" + "=" * 72)
    print(">>> ALL DAY 25 CAPSTONE VERIFICATIONS & TEST SUITES PASSED (100%) <<<")
    print("=" * 72)
    return 0


if __name__ == "__main__":
    sys.exit(main())
