from __future__ import annotations
from datetime import datetime, timezone
from typing import List, Optional
from sqlalchemy import (
    Column,
    Integer,
    String,
    Float,
    DateTime,
    ForeignKey,
    Text,
)
from sqlalchemy.orm import relationship
try:
    from sqlalchemy.dialects.postgresql import TSVECTOR
except ImportError:
    TSVECTOR = Text  # type: ignore

from ..db.session import Base


class Product(Base):
    __tablename__ = "products"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False, index=True)
    price = Column(Float, nullable=False)
    category = Column(String, nullable=False, index=True)
    image = Column(String, nullable=False)
    description = Column(Text, nullable=True, default="")
    stock = Column(Integer, nullable=False, default=50)
    search_vector = Column(TSVECTOR, nullable=True)

    order_items = relationship("OrderItem", back_populates="product")

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "price": self.price,
            "category": self.category,
            "image": self.image,
            "description": self.description or "",
            "stock": self.stock if self.stock is not None else 50,
        }


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    email = Column(String, unique=True, nullable=False, index=True)
    password_hash = Column(String, nullable=False)
    role = Column(String, nullable=False, default="shopper")
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    orders = relationship("Order", back_populates="user")


class Order(Base):
    __tablename__ = "orders"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True, index=True)
    email = Column(String, nullable=False, index=True)
    total = Column(Float, nullable=False)
    status = Column(String, nullable=False, default="pending")
    full_name = Column(String, nullable=True)
    phone = Column(String, nullable=True)
    address = Column(String, nullable=True)
    city = Column(String, nullable=True)
    state = Column(String, nullable=True)
    pincode = Column(String, nullable=True)
    payment_method = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    user = relationship("User", back_populates="orders")
    items = relationship("OrderItem", back_populates="order", cascade="all, delete-orphan", lazy="selectin")

    def to_dict(self):
        return {
            "id": self.id,
            "user_id": self.user_id,
            "email": self.email,
            "total": self.total,
            "status": self.status,
            "full_name": self.full_name,
            "phone": self.phone,
            "address": self.address,
            "city": self.city,
            "state": self.state,
            "pincode": self.pincode,
            "payment_method": self.payment_method,
            "created_at": str(self.created_at) if self.created_at else "",
            "items": [item.to_dict() for item in self.items] if self.items else [],
        }


class OrderItem(Base):
    __tablename__ = "order_items"

    id = Column(Integer, primary_key=True, index=True)
    order_id = Column(Integer, ForeignKey("orders.id"), nullable=False, index=True)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False, index=True)
    product_name = Column(String, nullable=True)
    quantity = Column(Integer, nullable=False)
    unit_price = Column(Float, nullable=False)

    order = relationship("Order", back_populates="items")
    product = relationship("Product", back_populates="order_items")

    def to_dict(self):
        return {
            "id": self.id,
            "product_id": self.product_id,
            "name": self.product_name or (self.product.name if self.product else ""),
            "quantity": self.quantity,
            "unit_price": self.unit_price,
        }


class ChatMessage(Base):
    __tablename__ = "chat_messages"

    id = Column(Integer, primary_key=True, index=True)
    sender_email = Column(String, nullable=False, index=True)
    sender_name = Column(String, nullable=False)
    sender_role = Column(String, nullable=False)
    recipient_email = Column(String, nullable=False, index=True)
    message = Column(Text, nullable=False)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    def to_dict(self):
        return {
            "id": self.id,
            "sender_email": self.sender_email,
            "sender_name": self.sender_name,
            "sender_role": self.sender_role,
            "recipient_email": self.recipient_email,
            "text": self.message,
            "created_at": str(self.created_at) if self.created_at else "",
        }
