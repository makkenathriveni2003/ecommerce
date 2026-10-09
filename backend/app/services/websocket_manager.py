import asyncio
import json
import logging
from typing import Any
from fastapi import WebSocket

logger = logging.getLogger("websocket_manager")


class ConnectionManager:
    def __init__(self) -> None:
        self.active_connections: dict[WebSocket, dict[str, Any]] = {}
        self._lock = asyncio.Lock()

    async def connect(self, websocket: WebSocket, user_info: dict[str, Any]) -> None:
        await websocket.accept()
        async with self._lock:
            self.active_connections[websocket] = user_info
        logger.info(
            "WebSocket connected: %s (%s)",
            user_info.get("email"),
            user_info.get("role"),
        )
        await self.send_personal_message(
            {
                "type": "CONNECTION_ESTABLISHED",
                "data": {
                    "user": user_info,
                    "admin_online": self.is_admin_online(),
                    "message": "Connected to ShopZone Live WebSocket Service",
                },
            },
            websocket,
        )
        await self._broadcast_presence()

    async def disconnect(self, websocket: WebSocket) -> None:
        async with self._lock:
            user = self.active_connections.pop(websocket, None)
        if user:
            logger.info("WebSocket disconnected: %s", user.get("email"))
        await self._broadcast_presence()

    def update_user(self, websocket: WebSocket, user_info: dict[str, Any]) -> None:
        if websocket in self.active_connections:
            self.active_connections[websocket] = user_info

    async def send_personal_message(self, message: dict[str, Any], websocket: WebSocket) -> None:
        try:
            await websocket.send_text(json.dumps(message))
        except Exception as error:
            logger.debug("Failed to send message to websocket: %s", error)

    async def broadcast_to_user(self, email: str, message: dict[str, Any]) -> None:
        target_email = email.strip().lower()
        stale_sockets: list[WebSocket] = []
        payload = json.dumps(message)

        for ws, info in list(self.active_connections.items()):
            if info.get("email", "").strip().lower() == target_email:
                try:
                    await ws.send_text(payload)
                except Exception:
                    stale_sockets.append(ws)

        if stale_sockets:
            async with self._lock:
                for s in stale_sockets:
                    self.active_connections.pop(s, None)

    async def broadcast_to_admins(self, message: dict[str, Any]) -> None:
        stale_sockets: list[WebSocket] = []
        payload = json.dumps(message)

        for ws, info in list(self.active_connections.items()):
            if info.get("role") == "admin":
                try:
                    await ws.send_text(payload)
                except Exception:
                    stale_sockets.append(ws)

        if stale_sockets:
            async with self._lock:
                for s in stale_sockets:
                    self.active_connections.pop(s, None)

    async def broadcast_to_all(self, message: dict[str, Any]) -> None:
        stale_sockets: list[WebSocket] = []
        payload = json.dumps(message)

        for ws in list(self.active_connections.keys()):
            try:
                await ws.send_text(payload)
            except Exception:
                stale_sockets.append(ws)

        if stale_sockets:
            async with self._lock:
                for s in stale_sockets:
                    self.active_connections.pop(s, None)

    async def broadcast_order_update(
        self, order_data: dict[str, Any], customer_email: str
    ) -> None:
        payload = {
            "type": "ORDER_UPDATE",
            "data": order_data,
        }
        await self.broadcast_to_user(customer_email, payload)
        await self.broadcast_to_admins(payload)

    async def broadcast_notification(
        self, notification_data: dict[str, Any], customer_email: str
    ) -> None:
        payload = {
            "type": "NOTIFICATION",
            "data": notification_data,
        }
        await self.broadcast_to_user(customer_email, payload)

    async def broadcast_chat_message(self, chat_data: dict[str, Any]) -> None:
        payload = {
            "type": "CHAT_MESSAGE",
            "data": chat_data,
        }
        sender_email = chat_data.get("sender_email", "").strip().lower()
        recipient_email = chat_data.get("recipient_email", "").strip().lower()
        sender_role = chat_data.get("sender_role", "")

        await self.broadcast_to_admins(payload)
        if sender_role == "admin" and recipient_email and recipient_email != "admin":
            await self.broadcast_to_user(recipient_email, payload)
        elif sender_role != "admin":
            await self.broadcast_to_user(sender_email, payload)

    async def _broadcast_presence(self) -> None:
        admin_count = sum(
            1 for info in self.active_connections.values() if info.get("role") == "admin"
        )
        shopper_emails = sorted(
            {
                info.get("email")
                for info in self.active_connections.values()
                if info.get("email") and info.get("role") != "admin"
            }
        )
        presence = {
            "type": "PRESENCE_UPDATE",
            "data": {
                "admin_online": admin_count > 0,
                "online_shoppers": shopper_emails,
                "total_connections": len(self.active_connections),
            },
        }
        await self.broadcast_to_all(presence)

    def is_admin_online(self) -> bool:
        return any(info.get("role") == "admin" for info in self.active_connections.values())


websocket_manager = ConnectionManager()
