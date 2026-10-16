# Day 25 Capstone – PostgreSQL Connection Pooling & Tuning

## 1. Overview & Architectural Motivation

In high-concurrency production web services, **database connection management** is one of the most critical determinants of system stability and throughput. 

Without connection pooling, every incoming HTTP request:
1. Performs a 3-way TCP handshake with the PostgreSQL database.
2. Negotiates TLS encryption.
3. Authenticates credentials and allocates memory in PostgreSQL for a new backend worker process.
4. Executes the query and tears down the connection.

This lifecycle introduces **25–45 ms of connection overhead per query**. Under 50–100 concurrent requests, PostgreSQL quickly exceeds its connection limits, crashing or dropping connections.

```
[ UNPOOLED (High Latency & Crashes) ]
Request 1 ──► [ TCP Handshake ] ──► [ Auth ] ──► [ Query ] ──► [ Teardown ]
Request 2 ──► [ TCP Handshake ] ──► [ Auth ] ──► [ Query ] ──► [ Teardown ]
Request N ──► [ Connection Refused / Max Pool Limit Exceeded ]

[ POOLED WITH SQLAlchemy QueuePool (Sub-Millisecond Reuse) ]
Requests ──► [ SQLAlchemy QueuePool (20 Persistent Sockets) ] ──► PostgreSQL
             ├── Reuses pre-warmed sockets (< 1 ms latency)
             ├── Bursts up to 30 overflow connections
             └── Validates socket health before checkout (pool_pre_ping)
```

---

## 2. QueuePool Configuration & Parameter Tuning

In `backend/app/db/session.py` and `backend/app/core/config.py`, the database engine is configured with an enterprise-grade `QueuePool`:

```python
engine = create_engine(
    DATABASE_URL,
    connect_args=connect_args,
    pool_size=settings.DB_POOL_SIZE,        # Default: 20
    max_overflow=settings.DB_MAX_OVERFLOW,  # Default: 30
    pool_timeout=settings.DB_POOL_TIMEOUT,  # Default: 30 seconds
    pool_recycle=settings.DB_POOL_RECYCLE,  # Default: 1800 seconds (30 mins)
    pool_pre_ping=settings.DB_POOL_PRE_PING,# Default: True
    echo=False,
)
```

### Parameter Breakdown & Sizing Rationale

| Parameter | Configured Value | Engineering Rationale |
|---|---|---|
| **`pool_size`** | `20` | Base number of persistent TCP connections kept open in memory. Eliminates TCP handshakes for regular traffic. |
| **`max_overflow`** | `30` | Number of additional temporary connections allowed during peak bursts. Total peak connections = `pool_size + max_overflow` = **50**. |
| **`pool_timeout`** | `30` | Maximum time (in seconds) a request will wait for a connection to be released back to the pool before raising `TimeoutError`. |
| **`pool_recycle`** | `1800` | Automatically closes and re-establishes connections that have been idle for 30 minutes. Prevents drops from database firewalls or cloud NAT timeouts. |
| **`pool_pre_ping`** | `True` | Executes a lightweight `SELECT 1` ping before handing a connection to the application. If the connection was terminated by PostgreSQL, it is safely replaced without throwing a 500 error to the user. |

---

## 3. Sizing Formula for Multi-Worker Production Deployments

When running multi-worker Gunicorn servers, each worker process maintains its own independent connection pool:

$$\text{Max DB Connections Required} = (\text{Gunicorn Workers} \times (\text{pool\_size} + \text{max\_overflow})) + \text{Celery Concurrency}$$

For our production deployment:
- **Gunicorn Workers**: 4
- **Per-Worker `pool_size`**: 20
- **Per-Worker `max_overflow`**: 30 (peak total = 50 per worker)
- **PostgreSQL Server `max_connections`**: Configured to `200` in PostgreSQL production configuration, ensuring headroom for administrative maintenance, backups, and background Celery workers.

---

## 4. Pool Health Inspection & Observability

To monitor connection pool utilization in real time, `backend/app/db/session.py` provides `get_db_pool_status()`, which is directly surfaced in the `/health` endpoint:

```json
{
  "status": "ok",
  "service": "shopzone-api",
  "components": {
    "database": "healthy",
    "redis": "healthy",
    "connection_pool": "healthy"
  },
  "database_pool": {
    "engine": "postgres",
    "pool_type": "QueuePool",
    "pool_size": 20,
    "checked_in": 19,
    "checked_out": 1,
    "overflow": 0,
    "max_overflow": 30,
    "pool_timeout": 30,
    "pool_recycle": 1800,
    "pool_pre_ping": true
  }
}
```

This allows monitoring systems (Prometheus, CloudWatch, Datadog) to alert developers when `checked_out` approaches `pool_size + max_overflow`, preventing pool starvation before users experience timeouts.
