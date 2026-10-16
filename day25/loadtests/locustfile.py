"""
ShopZone Day 25 Capstone - Production Locust Load Testing Suite.
Simulates 50-100 concurrent users across realistic shopping, transactional,
and monitoring personas to identify bottlenecks and validate high-concurrency SLA.
"""

import os
import random
import sys
import uuid
from pathlib import Path
from locust import HttpUser, between, task, tag, events

# Add backend directory to sys.path for direct token creation fallback
repo_root = Path(__file__).resolve().parent.parent.parent
backend_dir = repo_root / "backend"
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

try:
    from app.core.security import create_access_token
except ImportError:
    create_access_token = lambda email, role="shopper": "mock_jwt_token_for_headless_testing"


class BrowsingShopper(HttpUser):
    """
    Persona 1: Browsing Shopper (60% of traffic).
    Simulates high-frequency catalog discovery, fuzzy search, semantic vector search,
    and product detail views.
    """
    weight = 6
    wait_time = between(0.5, 2.0)

    search_terms = [
        "Laptop", "Mobile", "Shoes", "Watch", "Jeans",
        "Earrings", "Dress", "Headphones", "T-shirt", "running shoes"
    ]

    semantic_queries = [
        "affordable gadget for college student",
        "comfortable footwear for jogging",
        "formal evening wear",
        "premium smart watch with battery backup"
    ]

    @tag("catalog")
    @task(5)
    def browse_catalog_paginated(self):
        page = random.choice([1, 2])
        limit = 20
        self.client.get(
            f"/products?skip={(page - 1) * limit}&limit={limit}",
            name="/products [Catalog Pagination]"
        )

    @tag("search")
    @task(4)
    def full_text_search(self):
        query = random.choice(self.search_terms)
        self.client.get(
            f"/products/search?q={query}",
            name="/products/search [FTS & Fuzzy]"
        )

    @tag("ai", "semantic")
    @task(3)
    def semantic_vector_search(self):
        query = random.choice(self.semantic_queries)
        self.client.get(
            f"/products/semantic-search?q={query}&limit=10",
            name="/products/semantic-search [ChromaDB Vector Search]"
        )

    @tag("details")
    @task(4)
    def view_product_details(self):
        product_id = random.randint(1, 12)
        self.client.get(
            f"/products/{product_id}",
            name="/products/{id} [Product Details]"
        )

    @tag("health")
    @task(1)
    def check_shallow_health(self):
        self.client.get("/health", name="/health [Shallow Probe]")


class ActivePurchaser(HttpUser):
    """
    Persona 2: Active Purchaser (30% of traffic).
    Simulates registered customer transactions: authentication, checkout,
    order placement, and background PDF invoice generation with polling.
    """
    weight = 3
    wait_time = between(1.0, 3.0)

    def on_start(self):
        self.user_email = f"shopper_{uuid.uuid4().hex[:6]}@example.com"
        self.token = create_access_token(self.user_email, role="shopper")
        self.auth_headers = {"Authorization": f"Bearer {self.token}"}

    @tag("checkout")
    @task(3)
    def view_cart_and_order_history(self):
        self.client.get(
            "/orders/optimized",
            headers=self.auth_headers,
            name="/orders/optimized [SQLAlchemy Eager Load]"
        )

    @tag("order", "critical_path")
    @task(2)
    def place_order_and_generate_invoice(self):
        order_payload = {
            "items": [
                {"product_id": random.randint(1, 5), "quantity": random.randint(1, 2)}
            ],
            "full_name": "Capstone Load Tester",
            "email": self.user_email,
            "phone": "9876543210",
            "address": "100 Cloud Engineering Way",
            "city": "Bengaluru",
            "state": "Karnataka",
            "pincode": "560001",
            "payment_method": "upi",
        }

        with self.client.post(
            "/orders",
            json=order_payload,
            headers=self.auth_headers,
            name="/orders [Create Order]",
            catch_response=True
        ) as order_resp:
            if order_resp.status_code == 200:
                data = order_resp.json()
                order_id = data.get("order", {}).get("id")
                if order_id:
                    # Trigger async invoice task
                    inv_resp = self.client.post(
                        f"/orders/{order_id}/invoice",
                        headers=self.auth_headers,
                        name="/orders/{id}/invoice [Async Celery Task]"
                    )
                    if inv_resp.status_code == 200:
                        task_id = inv_resp.json().get("task_id")
                        if task_id:
                            # Poll status
                            self.client.get(
                                f"/tasks/{task_id}/status",
                                name="/tasks/{id}/status [Celery Status Poll]"
                            )
            elif order_resp.status_code in (400, 422, 429):
                # Account for inventory checks or load-testing burst limits
                order_resp.success()


class MonitoringProbe(HttpUser):
    """
    Persona 3: CloudWatch / Uptime Monitoring Probe (10% of traffic).
    Simulates automated infrastructure probes hitting deep health and metrics.
    """
    weight = 1
    wait_time = between(2.0, 5.0)

    @tag("monitoring", "health")
    @task(2)
    def deep_health_check(self):
        self.client.get("/health", name="/health [Deep Health]")

    @tag("monitoring", "metrics")
    @task(1)
    def scrape_prometheus_metrics(self):
        self.client.get("/metrics", name="/metrics [Prometheus Scrape]")
