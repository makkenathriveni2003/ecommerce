# Day 25 Capstone – Architectural Decision Records (ADRs)

This document records the foundational architectural decisions made during the engineering of the **ShopZone E-Commerce platform**, outlining the context, alternatives considered, chosen approach, and consequences.

---

## ADR-001: Selection of FastAPI as Core Backend Framework
- **Status**: Accepted
- **Context**: Needed a modern Python web framework capable of handling high-throughput REST APIs, asynchronous WebSockets, and Server-Sent Events (SSE) for AI token streaming.
- **Alternatives Considered**: Django, Flask, Tornado.
- **Decision**: Selected **FastAPI** built on Starlette and Pydantic.
- **Rationale**:
  - Native Python `async`/`await` support yielding exceptional concurrency performance.
  - Automatic OpenAPI 3.1 schema generation and interactive Swagger UI.
  - Strict type validation and serialization via Pydantic v2.
  - Native support for Server-Sent Events (streaming AI responses) and WebSockets.

---

## ADR-002: Dual Database Engine Architecture (PostgreSQL & SQLite Fallback)
- **Status**: Accepted
- **Context**: The application needed to deploy to enterprise container environments (AWS EC2 with PostgreSQL 16) and ephemeral/serverless environments (Vercel serverless functions without persistent DB sockets).
- **Alternatives Considered**: Enforcing PostgreSQL-only, running SQLite-only.
- **Decision**: Implemented an automated database engine detection abstraction in `backend/app/db/database.py`.
- **Rationale**:
  - Production deployments on AWS EC2 connect to PostgreSQL 16 with ACID compliance, connection pooling, and pg_dump capabilities.
  - Serverless functions or local offline runs gracefully fall back to SQLite in `/tmp/ecommerce.db` without failing cold-starts.

---

## ADR-003: SQLAlchemy Connection Pooling with QueuePool
- **Status**: Accepted
- **Context**: Under 50–100 concurrent users, creating new database connections per request introduced 25–45 ms of connection overhead and caused PostgreSQL connection exhaustion errors.
- **Alternatives Considered**: External PgBouncer, NullPool, threading.Lock around single connection.
- **Decision**: Implemented SQLAlchemy **`QueuePool`** with `pool_size=20`, `max_overflow=30`, `pool_timeout=30`, `pool_recycle=1800`, and `pool_pre_ping=True`.
- **Rationale**:
  - Reuses pre-warmed database sockets, reducing query latency from ~35 ms to < 1 ms.
  - Eliminates connection storms and prevents 500 errors during traffic spikes.
  - Native integration with Python without requiring additional sidecar proxies.

---

## ADR-004: Gunicorn Master Process with Uvicorn Workers
- **Status**: Accepted
- **Context**: Single-process Uvicorn cannot take advantage of multiple CPU cores and is vulnerable to single-point-of-failure process crashes.
- **Alternatives Considered**: Running multiple standalone Uvicorn instances behind Nginx, Hypercorn.
- **Decision**: Configured **Gunicorn** process manager running `uvicorn.workers.UvicornWorker` with `(2 * Cores) + 1` workers.
- **Rationale**:
  - Automatic process supervision: restarts crashed workers automatically.
  - Zero-downtime reloads via `SIGHUP` signal.
  - Worker recycling via `max_requests=1000` with random jitter prevents long-term memory leaks.
  - Heartbeats mounted to RAM (`/dev/shm`) prevent disk stalls in Docker.

---

## ADR-005: Dual Role for Redis (AI Query Caching + Celery Broker)
- **Status**: Accepted
- **Context**: Needed an in-memory caching layer for expensive AI similarity searches and a reliable distributed task broker for background PDF invoice generation.
- **Alternatives Considered**: RabbitMQ + Memcached, AWS SQS + DynamoDB.
- **Decision**: Deployed **Redis 7** utilizing independent database partitions (`db 0` for Celery broker, `db 1` for result backend and AI cache).
- **Rationale**:
  - Consolidates infrastructure into a single lightweight, high-performance service container.
  - Sub-millisecond response times for AI prompt query caching.
  - `maxmemory 200mb` with `allkeys-lru` eviction guarantees bounded memory consumption.

---

## ADR-006: ChromaDB Vector Store with Hybrid Search
- **Status**: Accepted
- **Context**: Shoppers needed to find products using natural language intent ("outfit for beach wedding") rather than exact keyword matches.
- **Alternatives Considered**: Pinecone (cloud proprietary), pgvector extension in PostgreSQL, Elasticsearch.
- **Decision**: Implemented **ChromaDB** with persistent vector storage, combined with a hybrid fallback to PostgreSQL Full-Text Search.
- **Rationale**:
  - Embedded, self-hosted vector database with zero external subscription costs ($0.00 spend).
  - Fast cosine similarity retrieval with Top-K context injection into LLM prompts (RAG).
  - Transparent fallback to trigram and fuzzy search when queries contain specific model numbers.

---

## ADR-007: Decoupled Multi-Cloud Deployment (AWS EC2 + Vercel Edge)
- **Status**: Accepted
- **Context**: Needed ultra-fast global frontend page loads alongside containerized, persistent backend microservices.
- **Alternatives Considered**: Monolithic EC2 hosting both frontend and backend, full serverless on AWS Lambda.
- **Decision**: Deployed React 19 frontend to **Vercel Edge Network** and backend multi-container stack to **AWS EC2** behind Nginx SSL.
- **Rationale**:
  - Frontend static assets are served from global edge Points of Presence with sub-20ms TTFB.
  - Backend containers enjoy persistent filesystem storage, persistent Redis, ChromaDB, and background Celery workers that would time out on Lambda.
