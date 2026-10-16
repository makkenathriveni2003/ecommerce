# Day 25 Capstone – Docker Resource Management & Container Hardening

## 1. Why Resource Limits Matter in Production

Without explicit CPU and memory constraints:
1. **Noisy Neighbor Problem**: A runaway memory leak in an AI task or an unindexed query in PostgreSQL can consume 100% of host RAM.
2. **Kernel OOM Killer Chaos**: When physical RAM and swap are exhausted, the Linux Out-Of-Memory (OOM) killer arbitrarily kills processes based on `oom_score_adj`. In unconstrained setups, this frequently terminates critical system processes (like `dockerd`, `sshd`, or `postgres`).
3. **Log Disk Saturation**: Unrotated Docker container logs (`/var/lib/docker/containers/*/*.log`) grow indefinitely, eventually consuming 100% of the host disk, causing system lockup.

---

## 2. Production Resource Allocations (7-Container Stack)

In `day25/docker-compose.prod.yml`, every single container defines strict `deploy.resources.limits` and `deploy.resources.reservations`:

| Service | Container Image | CPU Limit | RAM Limit | CPU Reservation | RAM Reservation | Role & Sizing Rationale |
|---|---|---|---|---|---|---|
| **`postgres`** | `postgres:16-alpine` | **1.00 CPU** | **512 MB** | 0.25 CPU | 128 MB | Relational persistence, connection pool of 20–50 sockets. |
| **`redis`** | `redis:7-alpine` | **0.50 CPU** | **256 MB** | 0.10 CPU | 64 MB | In-memory caching, Celery broker, LRU eviction at 200MB. |
| **`chromadb`** | `chromadb/chroma:latest`| **1.00 CPU** | **512 MB** | 0.20 CPU | 128 MB | Vector similarity search for RAG catalog embeddings. |
| **`backend`** | `shopzone-backend:capstone`| **1.50 CPU** | **1024 MB** | 0.50 CPU | 256 MB | Gunicorn master + 4 Uvicorn workers handling API traffic. |
| **`celery_worker`**| `shopzone-backend:capstone`| **1.00 CPU** | **512 MB** | 0.25 CPU | 128 MB | Async invoice PDF generation & catalog reindexing. |
| **`celery_beat`** | `shopzone-backend:capstone`| **0.25 CPU** | **128 MB** | 0.05 CPU | 32 MB | Lightweight cron scheduler for periodic tasks. |
| **`nginx`** | `nginx:alpine` | **0.50 CPU** | **128 MB** | 0.10 CPU | 32 MB | Reverse proxy, TLS termination, SSE unbuffered streaming. |
| **TOTAL** | — | **5.75 CPU** | **3.07 GB** | **1.45 CPU** | **768 MB** | **Fits comfortably within standard AWS 2 vCPU / 4 GB instance (t3.medium / t4g.medium)** |

---

## 3. Limits vs. Reservations

- **`limits` (Ceiling)**: The maximum compute and memory the Linux kernel (`cgroups v2`) allows the container to use. If a container exceeds its memory limit, the kernel terminates only that specific container with an `OOMKilled` event, protecting the host and sibling containers.
- **`reservations` (Floor / Guaranteed)**: The minimum compute and memory Docker guarantees to allocate for the container. Docker Compose and Swarm will refuse to place the container if the host lacks these guaranteed resources.

---

## 4. Production Log Rotation Configuration

To prevent container logs from filling the host filesystem, all services are configured with Docker's `json-file` log driver with file size and file count caps:

```yaml
logging:
  driver: "json-file"
  options:
    max-size: "10m"
    max-file: "3"
```

- Each container produces a maximum of **3 log files** of **10 MB each**.
- Total log disk space per container is strictly bounded to **30 MB**, preventing disk exhaustion permanently.

---

## 5. Verification Commands

To validate Docker resource constraints locally or in CI/CD:

```powershell
# Run the automated static Docker resource validator
python day25/scripts/validate_docker_resources.py

# Inspect live container memory and CPU usage
docker stats --no-stream
```
