"""
Pydantic Schemas for ShopZone AI Assistant
Validates request payloads and structures responses.
"""
from __future__ import annotations

from typing import Any
from pydantic import BaseModel, Field


class AIChatHistoryItem(BaseModel):
    role: str = Field(..., description="Role: 'user' or 'assistant'")
    content: str = Field(..., max_length=1000, description="Message content")


class AIChatRequest(BaseModel):
    message: str = Field(
        ...,
        min_length=1,
        max_length=1000,
        description="The customer's question or search query",
        examples=["Which headphones are available under ₹3,000?"],
    )
    conversation_history: list[AIChatHistoryItem] = Field(
        default_factory=list,
        max_length=10,
        description="Previous turns for conversational context",
    )
    category: str | None = Field(
        default=None,
        description="Optional category filter (e.g. 'Electronics', 'Accessories')",
    )


class AICitation(BaseModel):
    product_id: int
    product_name: str
    category: str
    price: float
    stock: int
    url: str


class AIChatResponse(BaseModel):
    answer: str
    provider: str
    model: str
    citations: list[AICitation] = Field(default_factory=list)


class AIIndexResponse(BaseModel):
    products_indexed: int
    chunks_indexed: int
    total_vectors: int
    message: str


class AIStatusResponse(BaseModel):
    primary_provider: str
    fallback_providers: list[str]
    embedding_provider: str
    indexed_vectors_count: int
    configured_providers: dict[str, bool]
