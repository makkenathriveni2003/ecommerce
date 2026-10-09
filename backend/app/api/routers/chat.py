from typing import Any, List
from fastapi import APIRouter, Depends, Query
from ...core.security import require_authenticated_user
from ...schemas.schemas import ChatMessageCreate
from ...services.chat_service import get_chat_history, save_chat_message
from ...services.websocket_manager import websocket_manager

router = APIRouter(prefix="/chat", tags=["Chat"])


@router.get("/messages")
def get_chat_messages(
    customer: str | None = Query(default=None),
    user: dict[str, Any] = Depends(require_authenticated_user),
) -> list[dict[str, Any]]:
    return get_chat_history(user=user, customer=customer)


@router.post("/messages")
async def send_chat_message_rest(
    data: ChatMessageCreate,
    user: dict[str, Any] = Depends(require_authenticated_user),
) -> dict[str, Any]:
    chat_data = save_chat_message(
        user=user,
        recipient_email=data.recipient_email,
        text=data.message,
    )
    await websocket_manager.broadcast_chat_message(chat_data)
    return {"success": True, "message": "Message sent", "data": chat_data}
