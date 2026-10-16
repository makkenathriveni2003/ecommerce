# Day 25 Capstone – Production Server Architecture: Gunicorn with Uvicorn Workers

## 1. Why Gunicorn + Uvicorn Workers?

In development, running `uvicorn app.main:app --reload` is convenient. However, in production environments:
1. **Single-Process Failure Risk**: If an unhandled exception or C-extension segmentation fault crashes a single Uvicorn process, the entire API goes offline.
2. **CPU Core Underutilization**: Python's Global Interpreter Lock (GIL) prevents a single process from utilizing multiple CPU cores. A 4-core or 8-core server would leave 75%–85% of its compute capacity unused.
3. **Memory Creep**: Long-running Python processes often accumulate memory fragments over days of production traffic.

To address these challenges, **Gunicorn** acts as a robust **Process Manager / Supervisor**, while **Uvicorn** acts as the high-speed **ASGI Worker Engine**:

```
                       [ Incoming HTTPS Traffic ]
                                   │
                                   ▼
                      [ Nginx Reverse Proxy: 443 ]
                                   │
                                   ▼
                   [ Gunicorn Master Process (PID 1) ]
                   • Sits in unprivileged container
                   • Listens on port 8000
                   • Supervises worker health & heartbeats
                   • Handles OS signals (SIGHUP, SIGTERM)
                   ┌───────────────┼───────────────┐
                   ▼               ▼               ▼
           [ Uvicorn Worker 1 ] [ Uvicorn Worker 2 ] [ Uvicorn Worker N ]
           • Async Event Loop   • Async Event Loop   • Async Event Loop
           • uvloop + httptools • uvloop + httptools • uvloop + httptools
           • Recycles after 1k  • Recycles after 1k  • Recycles after 1k
```

---

## 2. Worker Sizing Formula

The standard production formula for I/O-bound web services with asynchronous event loops is:

$$\text{Workers} = (2 \times \text{CPU Cores}) + 1$$

In `day25/gunicorn_conf.py`, this is dynamically computed with bounded safety limits:

```python
cpu_count = multiprocessing.cpu_count()
default_workers = max(2, min((cpu_count * 2) + 1, 8))
workers = int(os.getenv("WEB_CONCURRENCY", default_workers))
```

- On a **2 vCPU cloud instance** (e.g. AWS `t3.medium` or `t4g.medium`): **5 workers**
- On a **4 vCPU cloud instance**: **8 workers** (capped to prevent container memory thrashing)

---

## 3. Worker Recycling to Prevent Memory Leaks

Long-running applications with AI models and complex libraries can experience gradual memory growth. Gunicorn prevents this through automated worker recycling:

```python
max_requests = int(os.getenv("GUNICORN_MAX_REQUESTS", "1000"))
max_requests_jitter = int(os.getenv("GUNICORN_MAX_REQUESTS_JITTER", "100"))
```

- After servicing approximately 1,000 requests ($\pm$ random jitter of 100 requests), a worker process gracefully finishes its current requests, terminates cleanly, and releases its memory back to the operating system.
- The Gunicorn master process immediately forks a fresh worker in its place with zero dropped requests.
- The random jitter prevents all workers from recycling at the exact same moment.

---

## 4. Shared Memory Heartbeats (`/dev/shm`) in Docker

In containerized Docker environments, Gunicorn uses temporary files to track worker heartbeats. By default, these files are written to `/tmp`, which lives on Docker's overlayfs storage driver, causing high disk I/O stalls during load bursts.

`day25/gunicorn_conf.py` mounts heartbeats directly to RAM:

```python
if os.path.exists("/dev/shm"):
    worker_tmp_dir = "/dev/shm"
```

This prevents false-positive worker timeouts under heavy concurrency.

---

## 5. Signal Handling & Zero-Downtime Reloads

Gunicorn supports POSIX operating system signals for production administration:

| Signal | Command | Action |
|---|---|---|
| **`SIGHUP`** | `kill -HUP <PID>` | Graceful zero-downtime reload. Re-reads config and restarts workers one by one. |
| **`SIGTERM`** | `kill -TERM <PID>` | Graceful shutdown. Workers finish active requests up to `graceful_timeout` (30s). |
| **`SIGINT`** | `kill -INT <PID>` | Immediate shutdown. |
| **`SIGUSR1`** | `kill -USR1 <PID>` | Reopens log files for logrotate coordination. |
| **`SIGTTIN` / `SIGTTOU`** | `kill -TTIN <PID>` | Dynamically scales worker processes up or down by 1 without downtime. |
