"""
Backward-compatibility adapter for websocket_manager module.
Re-exports from app.services.websocket_manager.
"""
from app.services.websocket_manager import ConnectionManager, websocket_manager as manager

__all__ = ["ConnectionManager", "manager"]
