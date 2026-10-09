"""
Backward-compatibility adapter for celery_app module.
Re-exports from app.tasks.celery_app.
"""
import sys
from pathlib import Path
backend_dir = str(Path(__file__).resolve().parent)
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

from app.tasks.celery_app import celery_app

__all__ = ["celery_app"]

if __name__ == "__main__":
    celery_app.start()
