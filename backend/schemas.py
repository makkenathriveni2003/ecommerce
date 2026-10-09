"""
Backward-compatibility adapter for schemas module.
Re-exports from app.schemas.
"""
from app.schemas.schemas import (
    LoginData,
    RegisterData,
    OrderItem,
    OrderData,
    ProductData,
    BulkImportResponse,
    OrderStatusData,
    ChatMessageCreate,
    ChatMessageOut,
    TaskTriggerRequest,
    TaskStatusResponse,
)

__all__ = [
    "LoginData",
    "RegisterData",
    "OrderItem",
    "OrderData",
    "ProductData",
    "BulkImportResponse",
    "OrderStatusData",
    "ChatMessageCreate",
    "ChatMessageOut",
    "TaskTriggerRequest",
    "TaskStatusResponse",
]
