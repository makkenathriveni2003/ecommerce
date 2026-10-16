"""
Root entrypoint for Render and cloud hosting platforms.
Ensures compatibility with multiple start commands:
  - uvicorn main:app --host 0.0.0.0 --port $PORT
  - uvicorn backend.app.main:app --host 0.0.0.0 --port $PORT
  - uvicorn backend.main:app --host 0.0.0.0 --port $PORT
"""
from __future__ import annotations
import os
import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
backend_dir = BASE_DIR / "backend"
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from backend.app.main import app

__all__ = ["app"]

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 10000))
    uvicorn.run("main:app", host="0.0.0.0", port=port)
