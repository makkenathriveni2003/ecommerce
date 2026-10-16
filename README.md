# ShopZone – Enterprise E-Commerce Platform
## Day 25 – CAPSTONE: FINAL PROJECT

Welcome to the **ShopZone E-Commerce Platform**, an enterprise-grade, cloud-native full-stack application completed as part of the **CoastalSeven Technologies Knowledge Factory Programme (Batch-7)** by **Makkena Thriveni**.

---

## 1. Cloud & System Architecture

```
                             [ Web & Mobile Users ]
                                        │
                    ┌───────────────────┴───────────────────┐
                    │ (HTTPS / TLS 1.3)                     │ (HTTPS / TLS 1.3)
                    ▼                                       ▼
       [ Vercel Edge CDN ]                      [ Nginx Reverse Proxy ]
       • React 19 + TypeScript SPA              (AWS EC2 - Ports 80 & 443)
       • Global Edge PoPs                       • Let's Encrypt TLS Termination
       • Static Asset Caching (1 Year)          • SSE Token Streaming (Buffering Off)
       • Zero-Config Edge Deploys               • WebSocket Upgrades (/ws)
       • https://day9-fastapi.vercel.app        • Security Headers (HSTS, CSP)
                    │                                       │
                    │ REST / WebSockets                     │ Private Docker Bridge
                    └───────────────────────────────────────┤
                                                            ▼
                                              [ Gunicorn + Uvicorn Workers ]
                                              • 4 Concurrency Worker Processes
                                              • Non-Root Container Execution
                                              • Worker Memory Recycling (1k req)
                                              • Structured JSON Logging
                                              • Sentry Error Tracking (PII Redacted)
                                              • Deep /health & /metrics Observability
                                                            │
                    ┌───────────────────────────────────────┼───────────────────────────────────────┐
                    ▼                                       ▼                                       ▼
       [ PostgreSQL 16 DB ]                    [ Redis 7 Cache & Broker ]              [ ChromaDB Vector DB ]
       • SQLAlchemy QueuePool (20+30)          • Celery Task Broker (db 0)             • Persistent Embedding Vectors
       • Auto pg_dump Snapshots                • Result Backend & Cache (db 1)         • Contextual RAG Product Match
       • SHA-256 Tamper Detection              • LRU Eviction Cap (200MB)              • Zero-Cost Semantic Search
       • 7-Day Retention Pruning               • Sub-3ms Query Cache Hit               • Cosine Similarity Retrieval
```

---

## 2. Core Engineering Capabilities

1. **High-Concurrency Performance & Load Testing (Day 25 Capstone)**:
   - Simulated 50–100 concurrent users using **Locust**.
   - Identified and eliminated P0 bottlenecks (connection starvation, worker CPU saturation, rate limit collisions).
   - Throughput improved by **+673%** (from 52 RPS to **405.3 RPS**).
   - Median latency: **14 ms**, p95 latency: **46 ms**, with **0.00% failure rate** across 12,000+ requests.
2. **PostgreSQL Database Connection Pooling (Day 25 Capstone)**:
   - Configured SQLAlchemy **`QueuePool`** (`pool_size=20`, `max_overflow=30`, `pool_timeout=30`, `pool_recycle=1800`, `pool_pre_ping=True`).
   - Slashed per-query connection overhead from 35 ms to **< 1 ms**.
   - Real-time pool metrics surfaced in `/health` for automated alerting.
3. **Production Server Architecture (Day 25 Capstone)**:
   - **Gunicorn** process supervisor managing **Uvicorn** async workers (`uvicorn.workers.UvicornWorker`).
   - Dynamic worker sizing: `workers = (2 * CPU Cores) + 1`.
   - Worker recycling (`max_requests=1000`) and shared RAM heartbeats (`/dev/shm`) in Docker.
4. **Docker Container Resource Governance (Day 25 Capstone)**:
   - Strict CPU and memory limits and reservations defined across all 7 production containers.
   - Bounded `json-file` log rotation with a 30MB cap per container.
5. **PostgreSQL Automated Backup & Disaster Recovery (Day 25 Capstone)**:
   - Automated compressed `pg_dump` backups with SHA-256 cryptographic checksums.
   - 7-day retention pruning and automated restoration verification drill.
   - Verified Recovery Time Objective (RTO) < 15 minutes, Recovery Point Objective (RPO) < 24 hours.
6. **Generative AI & RAG Architecture (Days 16–22)**:
   - ChromaDB vector store with cosine similarity matching.
   - Retrieval-Augmented Generation (RAG) with Google Gemini streaming via Server-Sent Events (SSE).
   - Anti-hallucination grounding guardrails and Redis sub-3ms query caching ($0.00 spend).
7. **Asynchronous Microservices & WebSockets (Days 10–15)**:
   - Celery background workers for automated PDF invoice generation and catalog reindexing.
   - Real-time bi-directional WebSockets (`/ws`) for live order tracking and support chat.
8. **Decoupled Multi-Cloud Deployment & Observability (Days 23–24)**:
   - React 19 SPA live on Vercel Edge CDN with HTTP/3.
   - Sentry error tracking with automated PII scrubbing in `before_send`.
   - Prometheus metrics exposition at `/metrics`.

---

## 3. Live Production URLs

| Resource | URL | Status |
|---|---|---|
| **Live Frontend Application** | [https://day9-fastapi.vercel.app](https://day9-fastapi.vercel.app) | **LIVE (HTTPS / Edge CDN)** |
| **Backend REST API** | [https://day9-fastapi.vercel.app/api/](https://day9-fastapi.vercel.app/api/) | **LIVE (HTTPS / REST)** |
| **Deep Health Probe** | [https://day9-fastapi.vercel.app/api/health](https://day9-fastapi.vercel.app/api/health) | **LIVE (HTTP 200)** |
| **Interactive API Documentation** | [https://day9-fastapi.vercel.app/api/docs](https://day9-fastapi.vercel.app/api/docs) | **LIVE (OpenAPI / Swagger)** |
| **Prometheus Exposition Endpoint** | [https://day9-fastapi.vercel.app/api/metrics](https://day9-fastapi.vercel.app/api/metrics) | **LIVE (Metrics Text)** |

---

## 4. Quick Start & Local Execution

### Local Python & Vite Execution

```powershell
# 1. Start Redis
.\redis\redis-server.exe .\redis\redis.windows.conf

# 2. Start Celery Worker
py -3.14 -m celery -A backend.app.tasks.celery_app worker --loglevel=info --pool=solo

# 3. Start FastAPI Backend (with Uvicorn or Gunicorn)
py -3.14 -m uvicorn app.main:app --app-dir backend --port 8000

# 4. Start React Frontend
cd frontend
npm run dev
```

### Production Docker Compose Stack

```bash
# Build and run complete multi-container production stack
docker compose -f day25/docker-compose.prod.yml up -d --build
```

---

## 5. Verification & Test Suite Execution

```powershell
# Run complete Day 25 Capstone verification suite (PowerShell)
.\day25\run_tests.ps1

# Run complete Day 25 verification suite (Batch)
day25\run_tests.bat

# Run static deliverables validation
python day25/scripts/validate_day25_capstone.py

# Run Docker resource validation
python day25/scripts/validate_docker_resources.py

# Run database disaster recovery drill
python day25/scripts/test_backup_recovery.py

# Run full backend test matrix
pytest backend/tests/ -v
```

---

## 6. Project Directory Layout

- `day25/`: **Capstone Final Project**:
  - `README.md`: Master Capstone technical guide.
  - `gunicorn_conf.py`: Production Gunicorn + Uvicorn worker process configuration.
  - `docker-compose.prod.yml`: Hardened 7-container stack with CPU/RAM limits.
  - `loadtests/`: Locust 50–100 user load test suite and benchmark CSV stats.
  - `scripts/`: Disaster recovery, backup, restore, load testing, and static validation scripts.
  - `docs/`: 10 specialized technical deep dives and Architectural Decision Records (ADRs).
  - `tests/`: Automated Capstone Pytest verification suite.
- `backend/`: FastAPI backend modular microservice architecture (`app/core/`, `app/api/`, `app/services/`, `app/db/`, `app/tasks/`).
- `frontend/`: React 19 + TypeScript + Vite responsive e-commerce web application.
- `.github/workflows/`: Automated CI/CD pipelines (`ci.yml`, `capstone-ci-cd.yml`).
