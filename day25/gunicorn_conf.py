"""
ShopZone Day 25 Capstone - Production Gunicorn Configuration.
Serves FastAPI application reliably with Uvicorn worker class,
automatic CPU-based concurrency, worker recycling, and graceful shutdown.
"""

import multiprocessing
import os
import sys

# Server Socket
host = os.getenv("HOST", "0.0.0.0")
port = os.getenv("PORT", "8000")
bind = f"{host}:{port}"
backlog = int(os.getenv("GUNICORN_BACKLOG", "2048"))

# Concurrency & Worker Management
# Sizing formula: (2 x Num_Cores) + 1, with bounds [2, 8] for container memory safety
cpu_count = multiprocessing.cpu_count()
default_workers = max(2, min((cpu_count * 2) + 1, 8))
workers = int(os.getenv("WEB_CONCURRENCY", default_workers))
worker_class = "uvicorn.workers.UvicornWorker"
worker_connections = int(os.getenv("GUNICORN_WORKER_CONNECTIONS", "1000"))

# Lifecycle, Timeouts & Memory Leak Prevention
timeout = int(os.getenv("GUNICORN_TIMEOUT", "120"))
keepalive = int(os.getenv("GUNICORN_KEEPALIVE", "5"))
graceful_timeout = int(os.getenv("GUNICORN_GRACEFUL_TIMEOUT", "30"))

# Worker recycling: restart worker after servicing N requests with random jitter
# Prevents memory creep over long runtimes in production containers
max_requests = int(os.getenv("GUNICORN_MAX_REQUESTS", "1000"))
max_requests_jitter = int(os.getenv("GUNICORN_MAX_REQUESTS_JITTER", "100"))

# Shared memory directory for worker heartbeats (Linux containers)
# Prevents disk I/O stalls on Docker storage drivers
if os.path.exists("/dev/shm"):
    worker_tmp_dir = "/dev/shm"

# Logging & Observability
accesslog = "-"
errorlog = "-"
loglevel = os.getenv("LOG_LEVEL", "info").lower()
access_log_format = '%(h)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s" %(D)sµs'

# Process Naming
proc_name = "shopzone_gunicorn_api"

# Lifecycle Hooks
def on_starting(server):
    server.log.info(
        f"[GUNICORN] Starting ShopZone API server on {bind} with {workers} workers (worker_class={worker_class})"
    )

def post_fork(server, worker):
    server.log.debug(f"[GUNICORN] Spawned worker process (pid: {worker.pid})")

def worker_int(worker):
    worker.log.info(f"[GUNICORN] Worker received INT/QUIT signal (pid: {worker.pid})")

def worker_abort(worker):
    worker.log.error(f"[GUNICORN] Worker received SIGABRT signal (pid: {worker.pid})")
