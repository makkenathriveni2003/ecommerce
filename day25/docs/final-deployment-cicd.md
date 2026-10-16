# Day 25 Capstone – Final Production Deployment & CI/CD Pipeline

## 1. Production Architecture Overview

The ShopZone production platform utilizes a modern **Decoupled Cloud Architecture**:
- **Frontend SPA**: React 19 + Vite 8 deployed to **Vercel's Global Edge Network** with HTTP/3, Brotli compression, and automated SSL.
- **Backend Services**: Multi-container Docker stack deployed to **AWS EC2 (Ubuntu 24.04 LTS)** fronted by an **Nginx Reverse Proxy** with automated Let's Encrypt TLS (Certbot).

```
                             [ Web & Mobile Users ]
                                        │
                    ┌───────────────────┴───────────────────┐
                    │ (HTTPS / TLS 1.3)                     │ (HTTPS / TLS 1.3)
                    ▼                                       ▼
       [ Vercel Edge CDN ]                      [ Nginx Reverse Proxy ]
       • React 19 + TypeScript                  (AWS EC2 - Ports 80 & 443)
       • Global Edge PoPs                       • Let's Encrypt TLS Termination
       • Static Cache & SPA Rewrites            • HTTP/2 + HSTS + Security Headers
       • https://day9-fastapi.vercel.app        • Unbuffered SSE / WebSocket Upgrades
                    │                                       │
                    │ REST API / WebSocket RPC              │ Private Docker Bridge
                    └───────────────────────────────────────┤
                                                            ▼
                                              [ Gunicorn + Uvicorn Backend ]
                                              • 4 Concurrency Workers
                                              • SQLAlchemy QueuePool (20+30)
                                              • Sentry Error Tracking
                                              • /health & /metrics Observability
```

---

## 2. GitHub Actions CI/CD Pipeline (`capstone-ci-cd.yml`)

The Capstone CI/CD workflow (`.github/workflows/capstone-ci-cd.yml`) enforces a **Green Build Policy** across 6 automated stages on every push and pull request:

```
[ Git Push / PR ]
       │
       ▼
[ Job 1: Lint & Quality ] ────► flake8, black, ruff, eslint, tsc --noEmit
       │
       ▼
[ Job 2: Backend Pytest Matrix ] ─► Unit, Integration, AI Focus, Day 25 Capstone
       │                            (Postgres 16 + Redis 7 Service Containers)
       ▼
[ Job 3: Frontend Build & Tests ] ─► Vitest suite + Vite production asset build
       │
       ├─────────────────────────────────────────┐
       ▼                                         ▼
[ Job 4: Disaster Recovery Drill ]   [ Job 5: Docker Validation & Build ]
• pg_dump snapshot creation          • validate_docker_resources.py
• sha256 checksum verification       • Multi-stage Dockerfile.backend build
• Database restoration drill         • Non-root image security scan
       │                                         │
       └────────────────────┬────────────────────┘
                            ▼
              [ Job 6: Deployment Verification ]
              • Live HTTPS endpoint probe (/health, /api/products)
              • SSL Certificate expiration verification
              • HSTS and security headers audit
```

---

## 3. Production Live URLs & Verification

| Service | Environment | Production URL | Status | SSL / Security |
|---|---|---|---|---|
| **Frontend Application** | Production (Vercel) | `https://day9-fastapi.vercel.app` | **LIVE (HTTP 200)** | TLS 1.3, Edge CDN, HTTP/2 |
| **Backend REST API** | Production (AWS/Vercel) | `https://day9-fastapi.vercel.app/api/` | **LIVE (HTTP 200)** | TLS 1.3, HSTS, PII Redaction |
| **Deep Health Probe** | Production Observability | `https://day9-fastapi.vercel.app/api/health` | **LIVE (HTTP 200)** | Deep PostgreSQL + Redis |
| **Interactive API Docs**| Production Swagger | `https://day9-fastapi.vercel.app/api/docs` | **LIVE (HTTP 200)** | OpenAPI 3.1 Spec |
| **Prometheus Metrics** | Production Metrics | `https://day9-fastapi.vercel.app/api/metrics` | **LIVE (HTTP 200)** | Prometheus Exposition Format |

---

## 4. HTTPS & Security Headers Configuration

Nginx enforces enterprise security headers on all responses:
- **HSTS**: `Strict-Transport-Security: max-age=63072000; includeSubDomains; preload`
- **X-Frame-Options**: `SAMEORIGIN` (prevents clickjacking)
- **X-Content-Type-Options**: `nosniff` (prevents MIME type confusion)
- **Referrer-Policy**: `strict-origin-when-cross-origin`
- **Content-Security-Policy**: Enforces trusted script sources and restricts frame embedding.
