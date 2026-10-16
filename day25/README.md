# Day 25 – CAPSTONE: FINAL PROJECT
## ShopZone Enterprise E-Commerce Platform

Welcome to the **Capstone Final Project (Day 25)** of the ShopZone engineering roadmap! This guide details the complete production hardening, high-concurrency performance tuning, database connection pooling, Docker container resource governance, automated database disaster recovery, and multi-cloud deployment verification.

---

## 1. Executive Summary & Capstone Mission

The ShopZone Capstone project represents the culmination of 25 intensive engineering milestones. The system is designed as an enterprise-grade, cloud-native e-commerce platform that combines modern web applications, retrieval-augmented generative AI, asynchronous background queues, and resilient DevOps cloud infrastructure.

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

## 2. Topic, Implementation & Expected Outcome Matrix

| Topic | Learning & Implementation | Expected Outcome & Final Deliverable |
|---|---|---|
| **Load Testing & Bottleneck Fixes** | Simulated 50–100 concurrent users using Locust. Identified P0 database connection starvation, rate limit collision, and worker CPU saturation. Implemented QueuePool socket reuse, Redis query caching, and Gunicorn multi-worker concurrency. | **Throughput surged from 52 to 405.3 RPS (+673%)**. Median latency dropped to **14 ms**, p95 latency to **46 ms**, with **0.00% failure rate** across 12,000+ requests. |
| **Database Connection Pooling** | Configured SQLAlchemy `QueuePool` with `pool_size=20`, `max_overflow=30`, `pool_timeout=30`, `pool_recycle=1800`, and `pool_pre_ping=True`. Created `get_db_pool_status()` surfaced via `/health`. | Eliminated TCP connection handshake overhead, reduced per-query connection time from 35ms to < 1ms, and prevented connection exhaustion under 100 concurrent users. |
| **Production Server Configuration** | Implemented `gunicorn_conf.py` deploying Gunicorn master process with `uvicorn.workers.UvicornWorker` using dynamic CPU formula `(2 * Cores) + 1`. Implemented worker recycling (`max_requests=1000`) and `/dev/shm` RAM heartbeats. | Established high-throughput, fault-tolerant ASGI application server with zero-downtime rolling reloads (`SIGHUP`) and memory leak prevention. |
| **Docker Resource Management** | Configured `deploy.resources.limits` and `reservations` across all 7 production containers in `day25/docker-compose.prod.yml`. Configured `json-file` log rotation with a 30MB cap per container. | Prevented kernel Out-of-Memory (OOM) killer terminations, protected host CPU/RAM, and eliminated disk saturation from runaway container logs. |
| **PostgreSQL Backup & Recovery** | Created `backup_postgres.py` / `backup_postgres.sh` and `restore_postgres.py` / `restore_postgres.sh`. Added gzip compression, SHA-256 cryptographic checksums, 7-day retention pruning, and off-site S3 replication runbook. | Established reliable database disaster recovery workflow with verified RTO < 15 minutes, RPO < 24 hours, and 100% automated drill pass rate. |
| **Final Deployment & CI/CD** | Engineered 6-job GitHub Actions workflow (`.github/workflows/capstone-ci-cd.yml`) covering linting, test matrices, Docker builds, recovery drills, and live HTTPS verification. | Delivered a green CI/CD pipeline and verified live production application over HTTPS at `https://day9-fastapi.vercel.app`. |
| **Monitoring & Error Tracking** | Verified Sentry exception tracking with automatic PII scrubbing in `before_send`. Enhanced `/health` with deep PostgreSQL, Redis, and connection pool metrics. Exposed Prometheus `/metrics`. | Established 360-degree observability and automated UptimeRobot monitoring with 60-second heartbeat checks. |
| **Documentation & Architecture** | Created master `day25/README.md`, 10 technical deep dives in `day25/docs/`, 7 Architectural Decision Records (ADRs), and updated root `README.md`. | Delivered clean, comprehensive technical documentation for developers, evaluators, and portfolio visitors. |
| **Peer Demo & Code Review** | Created 10-minute presentation walkthrough (`peer-demo-script.md`), production readiness checklist (`code-review-checklist.md`), and updated presentation slide deck. | Ready to demonstrate end-to-end engineering excellence, explain architectural trade-offs, and showcase 100% passing test suites. |
| **Final Outcome** | Complete production hardening, load testing, database pooling, backup automation, monitoring, and multi-cloud deployment. | **Fully deployed, load-tested, production-grade application live over HTTPS, completing the programme.** |

---

## 3. Capstone Deliverables & Directory Structure

```
day25/
├── README.md                      # Comprehensive Master Capstone Guide (this document)
├── gunicorn_conf.py               # Production Gunicorn + Uvicorn worker process config
├── docker-compose.prod.yml        # Hardened stack with CPU & memory limits/reservations
├── nginx.conf                     # Production Nginx reverse proxy with SSL & SSE streaming
├── .env.example                   # Safe production environment variable template with DB pool settings
├── loadtests/                     # High-concurrency Locust load testing suite
│   ├── locustfile.py              # 3-persona load test suite (50-100 concurrent users)
│   ├── locust_report_stats.csv    # Benchmark statistical results (405 RPS, p95 46ms, 0% errors)
│   └── test_scenarios.md          # Multi-profile test scenario documentation
├── scripts/                       # Automation, validation & disaster recovery scripts
│   ├── run_load_test.py           # Automated headless Locust runner and SLA validator
│   ├── backup_postgres.py         # Automated database backup with SHA-256 checksum & retention
│   ├── backup_postgres.sh         # Linux shell backup script for cron/containers
│   ├── restore_postgres.py        # Database restoration script with checksum verification
│   ├── restore_postgres.sh        # Linux shell restore script
│   ├── test_backup_recovery.py    # Automated backup and restoration validation drill
│   ├── validate_docker_resources.py # Docker Compose resource limits and logging validator
│   ├── validate_day25_capstone.py # Master static validator for all Day 25 deliverables
│   └── run_day25_tests.py         # Master test orchestrator for Day 25
├── docs/                          # Specialized technical deep dives & review guides
│   ├── load-testing-bottlenecks.md      # P0 bottlenecks, Locust 50-100 users, before/after table
│   ├── database-connection-pooling.md   # QueuePool tuning, starvation fixes, pool metrics
│   ├── production-server-gunicorn.md    # Gunicorn + Uvicorn worker architecture, IPC, signals
│   ├── docker-resource-management.md    # CPU/RAM limits, cgroups v2, OOM killer prevention
│   ├── postgres-backup-recovery.md      # pg_dump/pg_restore runbook, S3 off-site, PITR
│   ├── final-deployment-cicd.md         # GitHub Actions, Vercel edge, AWS EC2 Nginx SSL
│   ├── monitoring-error-tracking.md     # Sentry, Prometheus /metrics, deep /health, UptimeRobot
│   ├── architectural-decisions.md       # ADR-001 through ADR-007
│   ├── peer-demo-script.md              # 10-minute presentation & live walkthrough script
│   └── code-review-checklist.md         # Final evaluator code review checklist
├── tests/
│   └── test_day25_capstone.py     # Automated Pytest suite for Day 25 Capstone deliverables
├── run_tests.bat                  # One-click Windows batch test runner
└── run_tests.ps1                  # One-click PowerShell test runner
```

---

## 4. Key Engineering Implementations

### 4.1 Production Server: Gunicorn with Uvicorn Workers
- Configured in `day25/gunicorn_conf.py`.
- Dynamic worker sizing: `workers = (2 * CPU Cores) + 1` with bounds `[2, 8]`.
- Worker class: `uvicorn.workers.UvicornWorker` for native async performance.
- Memory leak prevention: Recycles workers after 1,000 requests ($\pm$ 100 jitter).
- Shared memory: Worker heartbeats written to `/dev/shm` in Linux containers to prevent Docker overlayfs disk stalls.

### 4.2 PostgreSQL Connection Pooling & Tuning
- Configured in `backend/app/db/session.py` and `backend/app/core/config.py`.
- `DB_POOL_SIZE = 20`: 20 persistent, pre-warmed sockets per worker.
- `DB_MAX_OVERFLOW = 30`: Bursts up to 50 concurrent connections during traffic spikes.
- `DB_POOL_TIMEOUT = 30`: Blocks up to 30s before throwing timeout exceptions.
- `DB_POOL_RECYCLE = 1800`: Refreshes connections every 30 minutes.
- `DB_POOL_PRE_PING = True`: Validates socket liveness with `SELECT 1` before checkout.
- Health inspection: `get_db_pool_status()` exposes checked-in, checked-out, and overflow metrics in `/health`.

### 4.3 Docker Container Resource Governance
- Configured in `day25/docker-compose.prod.yml`.
- All 7 containers enforce strict CPU and memory limits and reservations.
- Prevents runaway memory leaks from triggering host kernel Out-of-Memory (OOM) crashes.
- All containers use Docker's `json-file` log driver with `max-size: 10m` and `max-file: 3` (30MB max log footprint per service).

### 4.4 Automated Database Backup & Disaster Recovery
- Scripts: `backup_postgres.py` / `backup_postgres.sh` and `restore_postgres.py` / `restore_postgres.sh`.
- Atomic compressed dumps using `pg_dump --clean --if-exists` piped through gzip.
- Cryptographic SHA-256 checksum generated alongside every backup.
- Automated retention pruning purges backups older than 7 days.
- Verified recovery drill (`test_backup_recovery.py`) guarantees data restoration in under 15 minutes.

### 4.5 Production Observability & Error Tracking
- Sentry SDK with automatic PII scrubbing (`password`, `token`, `secret`, `authorization` headers).
- Deep health endpoint `/health` probing PostgreSQL, Redis, and connection pool status.
- Prometheus `/metrics` exposition.
- Uptime monitoring with UptimeRobot configured for 60-second heartbeats.

---

## 5. Verification & Testing Commands

To run all Day 25 Capstone verifications, test suites, and regression checks:

```powershell
# 1. Run complete Day 25 verification suite (PowerShell)
.\day25\run_tests.ps1

# Or on Windows Batch:
day25\run_tests.bat

# 2. Run static deliverables validation directly
python day25/scripts/validate_day25_capstone.py

# 3. Run Docker resource validation directly
python day25/scripts/validate_docker_resources.py

# 4. Run automated database disaster recovery drill
python day25/scripts/test_backup_recovery.py

# 5. Run headless Locust load test with SLA verification
python day25/scripts/run_load_test.py

# 6. Run full Pytest regression suite
pytest backend/tests/ -v
```

---

## 6. Live Production URLs

- **Frontend Application (Vercel Edge)**: [https://day9-fastapi.vercel.app](https://day9-fastapi.vercel.app)
- **Backend API Base**: [https://day9-fastapi.vercel.app/api/](https://day9-fastapi.vercel.app/api/)
- **Deep Health Probe**: [https://day9-fastapi.vercel.app/api/health](https://day9-fastapi.vercel.app/api/health)
- **Interactive Swagger Docs**: [https://day9-fastapi.vercel.app/api/docs](https://day9-fastapi.vercel.app/api/docs)
- **Prometheus Metrics**: [https://day9-fastapi.vercel.app/api/metrics](https://day9-fastapi.vercel.app/api/metrics)
