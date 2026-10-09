import json
import logging
import time
from datetime import datetime, timezone
from fastapi import APIRouter, Query, WebSocket, WebSocketDisconnect

from ...core.security import read_access_token
from ...db.database import database_connection
from ...services.websocket_manager import websocket_manager

logger = logging.getLogger("shopzone_websocket_router")
router = APIRouter(tags=["WebSocket"])


@router.websocket("/ws")
async def websocket_endpoint(
    websocket: WebSocket,
    token: str | None = Query(default=None),
) -> None:
    user_info = {
        "id": 0,
        "name": "Guest",
        "email": "guest",
        "role": "guest",
    }
    if token:
        try:
            email = read_access_token(token)
            with database_connection() as conn:
                db_user = conn.execute(
                    "SELECT id, name, email, role FROM users WHERE email = %s",
                    (email,),
                ).fetchone()
            if db_user:
                user_info = dict(db_user)
        except Exception:
            pass

    await websocket_manager.connect(websocket, user_info)
    try:
        while True:
            raw_text = await websocket.receive_text()
            try:
                message = json.loads(raw_text)
            except Exception:
                continue

            msg_type = message.get("type", "").upper()

            if msg_type == "PING":
                await websocket.send_text(json.dumps({"type": "PONG", "timestamp": int(time.time())}))

            elif msg_type == "AUTHENTICATE":
                auth_token = message.get("token")
                if auth_token:
                    try:
                        email = read_access_token(auth_token)
                        with database_connection() as conn:
                            db_user = conn.execute(
                                "SELECT id, name, email, role FROM users WHERE email = %s",
                                (email,),
                            ).fetchone()
                        if db_user:
                            user_info = dict(db_user)
                            websocket_manager.update_user(websocket, user_info)
                            await websocket.send_text(
                                json.dumps({
                                    "type": "AUTH_SUCCESS",
                                    "data": {"user": user_info},
                                    "message": "Authenticated successfully",
                                })
                            )
                    except Exception as err:
                        await websocket.send_text(
                            json.dumps({
                                "type": "AUTH_ERROR",
                                "message": str(err),
                            })
                        )

            elif msg_type == "CHAT_MESSAGE":
                text = (message.get("text") or message.get("message") or "").strip()
                if not text:
                    continue

                recipient = message.get("recipient_email", "admin").strip().lower()
                if user_info.get("role") != "admin":
                    recipient = "admin"

                sender_email = user_info.get("email", "guest")
                sender_name = user_info.get("name", "Guest")
                sender_role = user_info.get("role", "guest")

                with database_connection() as conn:
                    row = conn.execute(
                        """
                        INSERT INTO chat_messages (
                            sender_email, sender_name, sender_role, recipient_email, message
                        )
                        VALUES (%s, %s, %s, %s, %s)
                        RETURNING id, created_at
                        """,
                        (sender_email, sender_name, sender_role, recipient, text),
                    ).fetchone()

                msg_id = row["id"] if row else 0
                created_at = (
                    str(row["created_at"])
                    if row
                    else datetime.now(timezone.utc).isoformat()
                )
                chat_data = {
                    "id": msg_id,
                    "sender_email": sender_email,
                    "sender_name": sender_name,
                    "sender_role": sender_role,
                    "recipient_email": recipient,
                    "text": text,
                    "created_at": created_at,
                }
                await websocket_manager.broadcast_chat_message(chat_data)

    except WebSocketDisconnect:
        await websocket_manager.disconnect(websocket)
    except Exception as error:
        logger.debug("WebSocket connection error: %s", error)
        await websocket_manager.disconnect(websocket)
