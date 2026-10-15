# Day 24 – DevOps & AWS Deployment: ShopZone E-Commerce Platform

Welcome to **Day 24** of the ShopZone engineering roadmap! This guide details the complete DevOps, Cloud Infrastructure, and Observability architecture designed for enterprise-grade AWS and Vercel production deployment.

---

## 1. Production Architecture Overview

The ShopZone production architecture separates the client-facing frontend from the containerized backend services, utilizing high-performance cloud providers and the Principle of Least Privilege:

```
                            [ Web & Mobile Users ]
                                       │
                    ┌──────────────────┴──────────────────┐
                    │ (HTTPS)                             │ (HTTPS)
                    ▼                                     ▼
      [ Vercel Edge Network ]               [ Nginx Reverse Proxy ]
      • React 19 + Vite 8 SPA               (AWS EC2 - Ports 80 & 443)
      • Global Edge CDN                     • Let's Encrypt TLS Termination
      • Zero-Config Deployments             • SSE Streaming & WebSocket Upgrades
      • Static Asset Caching                • Security Headers (HSTS, CSP)
                    │                                     │
                    │ REST / WebSockets                   │ Private Docker Bridge
                    └─────────────────────────────────────┤
                                                          ▼
                                            [ FastAPI Backend API ]
                                            • Python 3.11/3.14 Non-Root Container
                                            • Structured JSON Logging
                                            • Prometheus Metrics (/metrics)
                                            • Shallow Health Probes (/health)
                                            • Sentry Exception Tracking
                                                          │
                    ┌─────────────────────────────────────┼──────────────────────────────────┐
                    ▼                                     ▼                                  ▼
      [ PostgreSQL 16 Database ]             [ Redis 7 Cache & Broker ]             [ ChromaDB Vector DB ]
      • Relational persistence               • Session store & cache                • AI RAG product vectors
      • Named persistent volume              • Celery task broker & beat            • Semantic search store
```

---

## 2. Day 24 Deliverables & Directory Structure

All Day 24 DevOps assets are organized in the project repository:

```
day24/
├── README.md                      # Complete beginner-friendly implementation guide
├── .env.example                   # Safe production environment variable template
├── nginx.conf                     # Production Nginx reverse proxy configuration
├── docker-compose.prod.yml        # Hardened multi-container production stack for EC2
├── prometheus.yml                 # Prometheus scrape configuration for /metrics
├── docs/                          # Specialized technical deep dives
│   ├── aws-ec2-setup.md           # Task 1: EC2 Ubuntu, SSH keys, Security Groups, Docker
│   ├── nginx-https-certbot.md     # Task 2: Nginx reverse proxy, DNS, Certbot SSL, HTTPS
│   ├── vercel-deployment.md       # Task 3: React Vite SPA deployment to Vercel & CORS
│   ├── sentry-logging-guide.md    # Task 4: Structured JSON logging, Request IDs, Sentry
│   ├── health-monitoring-uptimerobot.md # Task 5: /health checks, Prometheus, UptimeRobot
│   ├── aws-iam-least-privilege.md # Task 6: IAM users vs roles, minimal JSON policies
│   ├── s3-static-hosting.md       # Task 7: S3 static hosting, CloudFront OAC, private buckets
│   ├── load-balancing-autoscaling.md # Task 8: AWS ALB, Target Groups, Auto Scaling Groups
│   ├── cloudwatch-monitoring.md   # Task 9: CloudWatch agent, RAM/disk metrics, alarms
│   ├── deployment-troubleshooting.md # Task 10: 502 Bad Gateway, CORS, OOM, Certbot fixes
│   └── verification-checklist.md  # Local readiness vs cloud verification checklist
└── scripts/
    └── validate_day24_stack.py    # Static validator verifying all Day 24 assets
```

---

## 3. Step-by-Step Implementation Summary

### Task 1: AWS EC2 Deployment
- Dedicated multi-stage backend container running as non-root user (`thriveni`).
- EC2 setup instructions: Ubuntu 24.04 LTS, 2 GB swapfile, Docker Engine, and security groups.
- SSH access secured with ED25519 key pairs.
- Full details in [docs/aws-ec2-setup.md](docs/aws-ec2-setup.md).

### Task 2: Nginx Reverse Proxy and HTTPS
- Configured in `day24/nginx.conf`.
- Forwards REST API (`/api/`), real-time WebSockets (`/ws`), and unbuffered SSE AI streaming (`/ai/`).
- Includes Certbot ACME webroot challenge support and automated SSL certificate renewals.
- Full details in [docs/nginx-https-certbot.md](docs/nginx-https-certbot.md).

### Task 3: Vercel Frontend Deployment
- Analyzed existing frontend: React 19 with Vite 8 and TypeScript.
- Created `frontend/vercel.json` with SPA routing rewrites to `/index.html` and 1-year immutable caching for static assets.
- Documented environment variables (`VITE_API_URL`, `VITE_WS_URL`, `VITE_SENTRY_DSN`) and CORS coordination.
- Full details in [docs/vercel-deployment.md](docs/vercel-deployment.md).

### Task 4: Structured Logging and Sentry
- Implemented structured JSON logging in `backend/app/core/logging_config.py`.
- Emits timestamp, level, module, message, and `request_id`.
- Request-ID correlation middleware in `backend/app/middleware/request_logging.py` injects `X-Request-ID` into every response.
- Automated PII and credential scrubbing filters out passwords, tokens, and authorization headers.
- Sentry integration in `backend/app/core/sentry.py` and `frontend/src/utils/sentry.ts` with graceful fallback when DSN is empty.
- Full details in [docs/sentry-logging-guide.md](docs/sentry-logging-guide.md).

### Task 5: Health Checks and Monitoring
- Enhanced `/health` endpoint checks database (`SELECT 1`) and Redis (`PING`) without leaking credentials. Returns HTTP 200 when healthy, 503 when down.
- Implemented Prometheus metrics in `backend/app/core/metrics.py` exposed at `/metrics`.
- UptimeRobot instructions for 60-second automated availability monitoring.
- Full details in [docs/health-monitoring-uptimerobot.md](docs/health-monitoring-uptimerobot.md).

### Task 6: AWS IAM and Least Privilege
- Documented IAM best practices: never use AWS Root account for routine deployments.
- Explains IAM Users, Roles, Policies, and EC2 Instance Profiles with temporary credentials.
- Minimal JSON policies for CloudWatch, S3, and GitHub Actions OICD deployments.
- Full details in [docs/aws-iam-least-privilege.md](docs/aws-iam-least-privilege.md).

### Task 7: Amazon S3 Static Hosting
- Examined S3 static hosting vs CloudFront CDN with Origin Access Control (OAC).
- Security guidance explaining why production buckets should remain **100% private**.
- Full details in [docs/s3-static-hosting.md](docs/s3-static-hosting.md).

### Task 8: Load Balancing and Auto Scaling
- Application Load Balancer (ALB) architecture with Target Groups pointing to `/health`.
- EC2 Auto Scaling Group configuration, launch templates, and CPU target tracking policies.
- Architectural rule: keep database and Redis outside auto-scaling instances (e.g. Amazon RDS and ElastiCache).
- Full details in [docs/load-balancing-autoscaling.md](docs/load-balancing-autoscaling.md).

### Task 9: CloudWatch Monitoring
- Hypervisor metrics vs OS metrics requiring the Unified CloudWatch Agent (RAM & disk).
- Step-by-step CloudWatch Agent installation and JSON configuration.
- Recommended alarms: High CPU (>80%), High RAM (>85%), Hardware check failures, and 5xx errors via SNS.
- Full details in [docs/cloudwatch-monitoring.md](docs/cloudwatch-monitoring.md).

### Task 10: Final Integration & Troubleshooting
- Complete production integration architecture combining EC2, Docker Compose, Nginx, Vercel, Sentry, Prometheus, and CloudWatch.
- Step-by-step fixes for 502 Bad Gateway, CORS headers mismatch, Certbot ACME challenge timeouts, and OOM killer terminations.
- Full details in [docs/deployment-troubleshooting.md](docs/deployment-troubleshooting.md).

---

## 4. Local Verification & Running Automated Tests

To validate the entire Day 24 DevOps implementation locally:

```powershell
# 1. Run the Day 24 DevOps validation script
.venv\Scripts\python.exe day24\scripts\validate_day24_stack.py

# 2. Run the Day 24 automated Pytest suite
.venv\Scripts\python.exe -m pytest backend/tests/test_day24_devops.py -v

# 3. Run regression tests (Day 23 Docker + Day 22 AI Focus)
.venv\Scripts\python.exe day23\scripts\run_day23_tests.py

# 4. Verify frontend production build and typecheck
cd frontend
npm run typecheck
npm run build
```
