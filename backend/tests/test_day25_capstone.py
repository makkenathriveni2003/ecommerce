"""
ShopZone Day 25 Capstone - Production Readiness & Capstone Test Suite (Backend Reference).
"""

import sys
from pathlib import Path

repo_root = Path(__file__).resolve().parent.parent.parent
if str(repo_root) not in sys.path:
    sys.path.insert(0, str(repo_root))

from day25.tests.test_day25_capstone import *
