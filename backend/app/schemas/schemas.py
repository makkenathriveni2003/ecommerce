from typing import Literal, Optional
from pydantic import BaseModel, Field


class LoginData(BaseModel):
    email: str = Field(min_length=3, max_length=254)
    password: str = Field(min_length=8, max_length=128)


class RegisterData(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    email: str = Field(min_length=3, max_length=254)
    password: str = Field(min_length=8, max_length=128)


class OrderItem(BaseModel):
    product_id: int = Field(ge=1)
    quantity: int = Field(ge=1)


class OrderData(BaseModel):
    items: list[OrderItem] = Field(min_length=1)
    full_name: str = Field(min_length=1, max_length=150)
    email: str = Field(min_length=3, max_length=254)
    phone: str = Field(min_length=1, max_length=40)
    address: str = Field(min_length=1, max_length=500)
    city: str = Field(min_length=1, max_length=100)
    state: str = Field(min_length=1, max_length=100)
    pincode: str = Field(min_length=1, max_length=20)
    payment_method: Literal["cash_on_delivery", "card", "upi"]


class ProductData(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    price: float = Field(ge=0, allow_inf_nan=False)
    category: str = Field(min_length=1, max_length=100)
    image: str = Field(min_length=1, max_length=2048)
    description: str | None = Field(default="", max_length=5000)
    stock: int | None = Field(default=50, ge=0)


class BulkImportResponse(BaseModel):
    success: bool
    task_id: str
    status: str
    filename: str
    message: str


class OrderStatusData(BaseModel):
    status: Literal["pending", "processing", "shipped", "delivered", "cancelled"]


class ChatMessageCreate(BaseModel):
    recipient_email: str = Field(default="admin", max_length=254)
    message: str = Field(min_length=1, max_length=2000)


class ChatMessageOut(BaseModel):
    id: int
    sender_email: str
    sender_name: str
    sender_role: str
    recipient_email: str
    message: str
    created_at: str


class TaskTriggerRequest(BaseModel):
    steps: int = Field(default=8, ge=1, le=50)
    delay: float = Field(default=0.4, ge=0.05, le=5.0)
    name: str = Field(default="Sample Background Job", max_length=100)


class TaskStatusResponse(BaseModel):
    task_id: str
    status: str
    percent: int
    message: str
    result: object | None = None
    error: str | None = None
