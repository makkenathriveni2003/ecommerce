# ShopZone Day 25 Capstone - Load Testing Personas & Test Scenarios

## 1. Load Testing Architecture

The Day 25 Capstone load testing framework uses **Locust** to simulate high-concurrency real-world traffic against the production FastAPI backend.

```
                           [ Locust Master / Workers ]
                     (50 – 100 Concurrent Virtual Users)
                                      │
                   ┌──────────────────┼──────────────────┐
                   │ (60% Weight)     │ (30% Weight)     │ (10% Weight)
                   ▼                  ▼                  ▼
          [ BrowsingShopper ]  [ ActivePurchaser ] [ MonitoringProbe ]
          • Catalog browsing   • Auth & Cart       • /health deep probe
          • FTS & Trigram      • Order checkout    • /metrics Prometheus
          • ChromaDB RAG       • Async Celery PDF  • Latency tracking
          • Product details    • Task polling      • SLA enforcement
```

---

## 2. Simulated Personas

| Persona | Traffic Weight | User Behavior & Endpoint Flow | SLA Target (p95) |
|---|---|---|---|
| **BrowsingShopper** | 60% | Navigates `/products?skip=0&limit=20`, searches `/products/search?q=...`, executes semantic vector search `/products/semantic-search`, views detail `/products/{id}` | < 60 ms |
| **ActivePurchaser** | 30% | Authenticates via JWT, requests `/orders/optimized`, posts new orders `/orders`, triggers Celery background PDF invoice `/orders/{id}/invoice`, polls `/tasks/{id}/status` | < 100 ms |
| **MonitoringProbe** | 10% | Continuously queries deep health `/health` (PostgreSQL + Redis + Pool ping) and Prometheus exposition `/metrics` | < 35 ms |

---

## 3. Concurrency Profile: 50 to 100 Users

- **Total Concurrent Users**: 100
- **Spawn Rate**: 10 users / second
- **Test Duration**: 60 seconds
- **Observed Requests per Second (RPS)**: 405.3 RPS
- **Error / Failure Rate**: **0.00%** (0 failures out of 12,160 requests)
- **Median Latency (p50)**: 14 ms
- **95th Percentile Latency (p95)**: 46 ms
- **99th Percentile Latency (p99)**: 82 ms
