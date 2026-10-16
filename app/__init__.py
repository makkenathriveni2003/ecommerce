"""
Root app package providing seamless forwarding to backend/app.
Enables 'import app', 'import app.main', 'uvicorn app.main:app'.
"""
from __future__ import annotations
import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
backend_dir = BASE_DIR.parent / "backend"
backend_app_dir = backend_dir / "app"

if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

__path__ = [str(backend_app_dir)]

from backend.app.main import app

__all__ = ["app"]
