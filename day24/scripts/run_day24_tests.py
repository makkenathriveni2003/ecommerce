"""
ShopZone Day 24 DevOps & AWS Focus - Test & Validation Runner.
Executes static stack validation and automated Pytest test suites.
"""

import subprocess
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


def main():
    print("=" * 72)
    print("        RUNNING COMPLETE DAY 24 DEVOPS & OBSERVABILITY TEST SUITE")
    print("=" * 72)

    # 1. Run static validation
    val_script = DAY24_DIR / "scripts" / "validate_day24_stack.py"
    res1 = subprocess.run([sys.executable, str(val_script)])
    if res1.returncode != 0:
        print("Static validation failed.")
        return res1.returncode

    # 2. Run Day 24 Pytest Suite
    print("\n" + "=" * 72)
    print("        RUNNING DAY 24 PYTEST SUITE (backend/tests/test_day24_devops.py)")
    print("=" * 72)
    res2 = subprocess.run([
        sys.executable, "-m", "pytest",
        str(REPO_ROOT / "backend" / "tests" / "test_day24_devops.py"),
        "-v"
    ])
    if res2.returncode != 0:
        print("Day 24 Pytest suite failed.")
        return res2.returncode

    # 3. Run Day 23 & Day 22 Regression checks
    print("\n" + "=" * 72)
    print("        RUNNING DAY 23 DEVOPS & DAY 22 AI REGRESSION TESTS")
    print("=" * 72)
    day23_runner = REPO_ROOT / "day23" / "scripts" / "run_day23_tests.py"
    if day23_runner.exists():
        res3 = subprocess.run([sys.executable, str(day23_runner)])
        if res3.returncode != 0:
            print("Regression checks failed.")
            return res3.returncode

    print("\n" + "=" * 72)
    print(">>> ALL DAY 24 DEVOPS, DOCKER & REGRESSION TESTS PASSED (100%) <<<")
    print("=" * 72)
    return 0


if __name__ == "__main__":
    sys.exit(main())
