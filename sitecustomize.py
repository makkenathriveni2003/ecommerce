"""
Python sitecustomize hook.
Automatically executed by Python upon startup before any script or module (like uvicorn) runs.
Ensures backend/ is on sys.path so that:
  - import app
  - import app.main
  - import backend.app.main
  - import main
all resolve perfectly with zero configuration.
"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
backend_dir = ROOT / "backend"

if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
