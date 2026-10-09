"""
Backward-compatibility adapter for models module.
Re-exports from app.models.
"""
from app.models.models import Product, User, Order, OrderItem, ChatMessage

__all__ = ["Product", "User", "Order", "OrderItem", "ChatMessage"]
