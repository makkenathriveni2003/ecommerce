"""
Forwarder for app.main -> backend.app.main.
Ensures 'uvicorn app.main:app' loads cleanly.
"""
from __future__ import annotations
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
backend_dir = ROOT / "backend"
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

from backend.app.main import app

__all__ = ["app"]
