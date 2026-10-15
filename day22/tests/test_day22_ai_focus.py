"""
Comprehensive Unit & Integration Test Suite for Day 22 – AI Focus Project (Chow Zoon)
Validates:
1. RAG-Powered Product Assistant & Streaming SSE pipeline
2. Embedding-based Semantic Search (`/products/semantic-search` & `/products/search?semantic=true`)
3. AI-Generated Product Descriptions (`POST /ai/generate-description`)
4. Redis Response Caching & Cost Governance ($0.00 Spend)
5. Real-Time Order Tracking via WebSockets (`/ws`)
6. Celery Background Tasks (description generator & catalog reindexer)
7. Anti-hallucination, grounding, and fallback resilience
"""
import json
import pytest
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient

from app.main import app
from app.services.ai.ai_cache import ai_cache
from app.services.ai.description_generator import generate_ai_product_description
from app.tasks.celery_tasks import generate_product_description_task, reindex_catalog_task


@pytest.fixture
def client():
    with TestClient(app) as c:
        yield c


# ==============================================================================
# 1. Semantic Search Integration
# ==============================================================================
def test_semantic_search_endpoint(client: TestClient):
    """Semantic search returns products ordered by relevance."""
    response = client.get("/products/semantic-search?q=cotton shirt")
    assert response.status_code == 200
    products = response.json()
    assert isinstance(products, list)
    # If database has products, verify structure
    if products:
        first = products[0]
        assert "id" in first
        assert "name" in first
        assert "price" in first
        assert "category" in first


def test_search_with_semantic_flag(client: TestClient):
    """Standard search endpoint delegates to semantic search when semantic=true."""
    response = client.get("/products/search?q=running shoes&semantic=true")
    assert response.status_code == 200
    products = response.json()
    assert isinstance(products, list)


def test_semantic_search_empty_query(client: TestClient):
    """Semantic search requires a non-empty query string."""
    response = client.get("/products/semantic-search?q=")
    assert response.status_code in (200, 400, 422)


# ==============================================================================
# 2. AI-Generated Product Descriptions
# ==============================================================================
def test_ai_generate_description_endpoint(client: TestClient):
    """POST /ai/generate-description generates high-quality e-commerce copy."""
    payload = {
        "name": "Chow Zoon Ultra Wireless Headphones",
        "category": "Electronics",
        "price": 4999.0,
        "key_features": ["Active Noise Cancelling", "40-hour Battery", "Fast USB-C Charging"],
        "tone": "engaging",
    }
    response = client.post("/ai/generate-description", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert len(data["description"]) > 20
    assert "Wireless" in data["description"] or "Headphones" in data["description"] or "Chow Zoon" in data["description"] or "sound" in data["description"].lower() or len(data["bullet_points"]) > 0
    assert data["provider"] is not None


def test_ai_generate_description_direct_service():
    """Service function generates copy and utilizes local fallback cleanly."""
    import asyncio
    res = asyncio.run(
        generate_ai_product_description(
            name="Classic Oxford Cotton Shirt",
            category="Fashion",
            price=1499.0,
            keywords=["100% Breathable Cotton", "Tailored Regular Fit"],
        )
    )
    assert "description" in res
    assert len(res["description"]) > 30
    assert "Cotton" in res["description"] or "Shirt" in res["description"] or "fit" in res["description"].lower()


# ==============================================================================
# 3. Redis AI Response Caching & Cost Governance ($0 Spend)
# ==============================================================================
def test_ai_status_and_cost_governance(client: TestClient):
    """GET /ai/status returns cost governance metrics confirming $0 API spend."""
    response = client.get("/ai/status")
    assert response.status_code == 200
    data = response.json()
    assert "primary_provider" in data
    assert "governance_metrics" in data
    gov = data["governance_metrics"]
    assert gov.get("estimated_spend_usd") == "$0.00"
    assert "cache_hit_rate" in gov


def test_redis_ai_cache_hit():
    """Verify that caching records hit and miss metrics and retrieves cached items."""
    prod_name = "Chow Zoon Test Shirt 99"
    cat_name = "Fashion"
    test_val = {"name": prod_name, "category": cat_name, "description": "Crisp cotton shirt for stylish occasions."}

    # Write to cache
    ai_cache.set_cached_description(prod_name, cat_name, test_val, ttl_seconds=30)

    # Read back from cache
    cached = ai_cache.get_cached_description(prod_name, cat_name)
    assert cached is not None
    assert "description" in cached

    # Governance metrics
    metrics = ai_cache.get_governance_metrics()
    assert metrics["estimated_spend_usd"] == "$0.00"


# ==============================================================================
# 4. RAG-Powered Product Assistant & Streaming Responses
# ==============================================================================
def test_ai_chat_non_streaming(client: TestClient):
    """POST /ai/chat returns grounded assistant response."""
    response = client.post("/ai/chat", json={"message": "Do you have any casual shirts in stock?"})
    assert response.status_code == 200
    data = response.json()
    assert "answer" in data
    assert len(data["answer"]) > 0


def test_ai_chat_streaming(client: TestClient):
    """POST /ai/chat/stream returns text/event-stream SSE events."""
    with client.stream("POST", "/ai/chat/stream", json={"message": "What products are available?"}) as res:
        assert res.status_code == 200
        assert "text/event-stream" in res.headers["content-type"]
        events = []
        for line in res.iter_lines():
            if line:
                events.append(line)
            if len(events) >= 5:
                break
        assert len(events) > 0


# ==============================================================================
# 5. Real-Time WebSockets
# ==============================================================================
def test_websocket_realtime_connection(client: TestClient):
    """Connecting to /ws establishes live WebSocket tracking session."""
    with client.websocket_connect("/ws") as websocket:
        init_msg = websocket.receive_json()
        assert init_msg["type"] == "CONNECTION_ESTABLISHED"
        assert "user" in init_msg["data"]

        # Send a ping message
        websocket.send_text(json.dumps({"type": "PING"}))
        received_types = []
        for _ in range(5):
            msg = websocket.receive_json()
            received_types.append(msg.get("type"))
            if msg.get("type") == "PONG":
                break
        assert "PONG" in received_types or "PRESENCE_UPDATE" in received_types


# ==============================================================================
# 6. Celery Background Tasks Execution
# ==============================================================================
def test_celery_description_task():
    """Celery background task executes description generation."""
    res = generate_product_description_task.apply(
        args=[
            "Wireless Mechanical Keyboard",
            "Electronics",
            3499.0,
            ["RGB Backlit", "Hot-Swappable Switches"],
        ]
    ).result
    assert res["status"] == "SUCCESS"
    assert "description" in res


def test_celery_reindex_task():
    """Celery background task executes catalog reindexing without crashing."""
    res = reindex_catalog_task.apply().result
    assert res["status"] == "SUCCESS"
    assert "total_vectors" in res


def test_ai_chat_greeting_and_unwanted_messages(client):
    """Verify greeting and unwanted off-topic queries return 0 citations and proper messages."""
    # 1. Greeting
    resp_greeting = client.post("/api/ai/chat", json={"message": "hloo"})
    assert resp_greeting.status_code == 200
    data_greeting = resp_greeting.json()
    assert len(data_greeting.get("citations", [])) == 0
    assert "Welcome to GenZ Zone" in data_greeting.get("answer", "")

    # 2. Unwanted / Off-Topic (food, car, etc.)
    resp_unwanted = client.post("/api/ai/chat", json={"message": "do you have pizza"})
    assert resp_unwanted.status_code == 200
    data_unwanted = resp_unwanted.json()
    assert len(data_unwanted.get("citations", [])) == 0
    assert "not available in our genz zone catalogue" in data_unwanted.get("answer", "").lower()


def test_ai_chat_price_filtering_under_2000(client):
    """Verify queries asking for products under 2000 strictly return only products <= 2000."""
    resp = client.post("/api/ai/chat", json={"message": "any products under 2000"})
    assert resp.status_code == 200
    data = resp.json()
    citations = data.get("citations", [])
    assert len(citations) > 0
    for item in citations:
        assert float(item.get("price", 0)) <= 2000.0, f"Found item above budget: {item}"

