# Day 25 Capstone – Peer Demonstration & Technical Presentation Script

## 1. Demo Overview & Time Allocation (10 Minutes Total)

This runbook guides **Makkena Thriveni** through the **Capstone Final Project Demonstration** for mentors, evaluators, and peer reviewers.

| Segment | Topic | Duration | Key Talking Points & Live Actions |
|---|---|---|---|
| **Part 1** | Introduction & Cloud Architecture | 1.0 min | Problem statement, decoupled architecture (Vercel + AWS EC2), live URLs. |
| **Part 2** | React 19 UI & Real-Time WebSockets | 2.0 min | Responsive catalog, cart, live WebSocket order status notifications. |
| **Part 3** | Generative AI RAG & ChromaDB | 2.0 min | Semantic vector search, Gemini streaming SSE, grounding & hallucination guardrails. |
| **Part 4** | Asynchronous Celery & Redis | 1.5 min | Background invoice PDF generation, task status polling, Redis response cache. |
| **Part 5** | High-Concurrency Load Testing | 1.5 min | Locust 100-user simulation, P0 bottleneck fixes, before vs after benchmark table. |
| **Part 6** | Production Hardening & DevOps | 1.0 min | Gunicorn+Uvicorn workers, DB QueuePool, Docker CPU/RAM limits, Sentry/Prometheus. |
| **Part 7** | Database Backup & Recovery Drill | 1.0 min | Automated pg_dump, SHA-256 checksum validation, restoration drill. |
| **Part 8** | Q&A & Reviewer Verification | — | Open for technical questions and architecture defense. |

---

## 2. Speaker Script & Demonstration Walkthrough

### Part 1: Introduction & Architecture (Minute 0:00 – 1:00)
- **Speaker**: *"Good morning everyone! My name is Makkena Thriveni. Today, I am thrilled to present my Capstone Final Project: ShopZone—a production-grade, AI-powered e-commerce platform built over 25 intensive engineering days."*
- **Action**: Open browser to `https://day9-fastapi.vercel.app`.
- **Speaker**: *"ShopZone is built with a decoupled cloud architecture: The user-facing application is a React 19 SPA running on Vercel's Global Edge Network, communicating over secure HTTPS to our containerized FastAPI backend on AWS EC2 fronted by Nginx reverse proxy with Let's Encrypt TLS."*

### Part 2: React 19 Frontend & Real-Time WebSockets (Minute 1:00 – 3:00)
- **Action**: Demonstrate catalog browsing, filter by category ('Electronics', 'Accessories'), add a laptop and headphones to cart.
- **Speaker**: *"Our UI features smooth Zustand state management, instant search filtering, and responsive cart operations. When an order is placed, we establish a bidirectional WebSocket connection on `/ws` to deliver real-time order confirmation and tracking status directly to the customer without polling."*

### Part 3: Generative AI RAG & ChromaDB Semantic Search (Minute 3:00 – 5:00)
- **Action**: Type a natural language query in search: `"affordable gadget for college student"`.
- **Speaker**: *"Traditional keyword search fails when users don't know the exact product name. We built an AI RAG pipeline using ChromaDB vector embeddings. The backend converts the user's intent into vector space, queries ChromaDB for contextual similarity, and injects relevant product context into Google Gemini to stream real-time shopping recommendations via Server-Sent Events (SSE). We also enforce strict grounding to prevent model hallucinations."*

### Part 4: Asynchronous Processing & Caching (Minute 5:00 – 6:30)
- **Action**: Click "Checkout" and trigger invoice generation.
- **Speaker**: *"To ensure checkout requests complete in under 30 milliseconds, heavy workloads like PDF invoice generation are offloaded to asynchronous Celery workers backed by Redis. The user receives an instant task ID, and our client polls `/tasks/{id}/status` until completion. Additionally, frequent AI search queries are cached in Redis with a 1-hour TTL, slashing latency from 800ms to 3ms."*

### Part 5: High-Concurrency Load Testing (Minute 6:30 – 8:00)
- **Action**: Show `day25/loadtests/locust_report_stats.csv` or Locust benchmark results.
- **Speaker**: *"For Day 25, we load-tested the entire platform with Locust under 50 to 100 concurrent users. Initially, we uncovered critical P0 bottlenecks: database connection starvation and worker CPU saturation. By configuring SQLAlchemy QueuePool with 20 persistent sockets and deploying Gunicorn with 4 Uvicorn workers, our throughput surged by 673% from 52 RPS to 405 RPS, while p95 latency plummeted from 385ms to just 46ms with zero request failures across 12,000+ requests."*

### Part 6: Production Hardening & Docker Resource Limits (Minute 8:00 – 9:00)
- **Action**: Open `day25/docker-compose.prod.yml`.
- **Speaker**: *"Every component is hardened for enterprise production. All 7 Docker containers have strict CPU and memory limits to prevent Out-of-Memory crashes. Logs are automatically rotated with a 30MB cap per container. Observability is maintained via Sentry exception tracking with PII scrubbing, Prometheus `/metrics`, and deep `/health` checks that probe PostgreSQL and Redis."*

### Part 7: Database Backup & Recovery Drill (Minute 9:00 – 10:00)
- **Action**: Run `python day25/scripts/test_backup_recovery.py` in terminal.
- **Speaker**: *"Data resilience is non-negotiable. We implemented an automated backup workflow using `pg_dump` with high-ratio gzip compression, 7-day retention pruning, and cryptographic SHA-256 checksums to detect data corruption. As shown in our live automated disaster recovery drill, our backup and restoration workflow achieves 100% verified data consistency with an RTO of under 15 minutes."*
- **Closing**: *"Thank you to CoastalSeven Technologies and our mentors for an incredible 25-day journey. I'm now open to any questions!"*
