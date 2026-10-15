"""
Day 23 DevOps & AWS Focus - Test Runner Script
Executes all static validation, Docker Compose verification, and Pytest suites.
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


def main():
    print("=" * 70)
    print("      RUNNING COMPLETE DAY 23 DEVOPS & DOCKER TEST SUITE")
    print("=" * 70)

    # 1. Run static validation
    val_script = REPO_ROOT / "day23" / "scripts" / "validate_devops_stack.py"
    res1 = subprocess.run([sys.executable, str(val_script)])
    if res1.returncode != 0:
        print("Static validation failed.")
        return res1.returncode

    # 2. Run Day 23 Pytest Suite
    print("\n" + "=" * 70)
    print("      RUNNING PYTEST SUITE (backend/tests/test_day23_devops.py)")
    print("=" * 70)
    res2 = subprocess.run([
        sys.executable, "-m", "pytest",
        str(REPO_ROOT / "backend" / "tests" / "test_day23_devops.py"),
        "-v"
    ])
    if res2.returncode != 0:
        print("Pytest suite failed.")
        return res2.returncode

    # 3. Run Day 22 AI Focus Pytest Suite to guarantee zero regressions
    print("\n" + "=" * 70)
    print("      RUNNING DAY 22 AI FOCUS PYTEST SUITE (REGRESSION CHECK)")
    print("=" * 70)
    res3 = subprocess.run([
        sys.executable, "-m", "pytest",
        str(REPO_ROOT / "backend" / "tests" / "test_day22_ai_focus.py"),
        "-v"
    ])
    if res3.returncode != 0:
        print("Day 22 regression check failed.")
        return res3.returncode

    print("\n" + "=" * 70)
    print(">>> ALL DAY 23 DEVOPS & DAY 22 REGRESSION TESTS COMPLETED 100% <<<")
    print("=" * 70)
    return 0


if __name__ == "__main__":
    sys.exit(main())
