import os
import random
import sys
from pathlib import Path
from locust import HttpUser, task, between

# Import create_access_token directly for load test token generation
backend_dir = str(Path(__file__).resolve().parent.parent / "backend")
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

try:
    from app.core.security import create_access_token
except ImportError:
    create_access_token = lambda email: None


class ShopZoneUser(HttpUser):
    """
    Simulates realistic ShopZone shoppers under load:
    - Browsing product catalog (20 items/page)
    - Full-Text and Fuzzy Search (English dictionary + Trigram matching)
    - Viewing product detail pages
    - Checking health & ping
    - Reading order history with SQLAlchemy eager loading
    """
    wait_time = between(0.5, 2.0)

    search_terms = ["Laptop", "Mobile", "Shoes", "Watch", "Jeans", "Earrings", "Dress", "laptp", "hedphone"]

    def on_start(self):
        self.user_email = "shopper@example.com"
        self.token = create_access_token(self.user_email) if create_access_token else None

    @property
    def auth_headers(self):
        if self.token:
            return {"Authorization": f"Bearer {self.token}"}
        return {}

    @task(6)
    def browse_catalog(self):
        self.client.get("/products?limit=20", name="/products [Catalog]")

    @task(5)
    def search_products(self):
        query = random.choice(self.search_terms)
        self.client.get(f"/products/search?q={query}", name="/products/search [FTS & Fuzzy]")

    @task(4)
    def view_product_detail(self):
        # Pick from guaranteed seeded product IDs
        product_id = random.choice([1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12])
        self.client.get(f"/products/{product_id}", name="/products/{id} [Details]")

    @task(3)
    def get_optimized_order_history(self):
        if self.token:
            self.client.get("/orders/optimized", headers=self.auth_headers, name="/orders/optimized [SQLAlchemy Eager]")

    @task(2)
    def get_order_history(self):
        if self.token:
            self.client.get("/orders", headers=self.auth_headers, name="/orders [Raw History]")

    @task(1)
    def check_health(self):
        self.client.get("/", name="/ [Root Health]")
