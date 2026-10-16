# Day 25 Capstone – Production Monitoring & Error Tracking Architecture

## 1. Observability Stack Overview

The ShopZone production monitoring architecture provides **360-degree observability** across three pillars:
1. **Error Tracking & Exception Capture**: Sentry SDK with automatic PII and credential redaction.
2. **Deep Health Probes**: `/health` endpoint validating PostgreSQL, connection pool metrics, and Redis.
3. **Application Metrics Exposition**: Prometheus `/metrics` endpoint tracking request latencies, throughput, and error codes.
4. **External Uptime Monitoring**: Automated UptimeRobot heartbeat checks with multi-channel alerting.

```
                           [ Production Observability ]
                                        │
             ┌──────────────────────────┼──────────────────────────┐
             ▼                          ▼                          ▼
    [ Sentry SDK ]              [ Deep /health ]           [ Prometheus /metrics ]
    • Exception captures        • DB SELECT 1              • http_requests_total
    • Stack trace context       • Redis PING               • http_request_duration_seconds
    • PII / Password filter     • Pool checkin/out counts  • Active connections
    • Zero crash on empty DSN   • 200 (OK) / 503 (Down)    • Scraped every 15s
```

---

## 2. Sentry Error Tracking with Automated PII Scrubbing

In `backend/app/core/sentry.py`, Sentry is configured with privacy-safe exception tracking:
- **Graceful Fallback**: If `SENTRY_DSN` is empty (in local development or offline test environments), the SDK logs a debug message and disables itself without throwing exceptions.
- **`before_send` PII Scrubbing**: Filters out sensitive data before any packet leaves the server:
  - Redacts `password`, `token`, `secret`, `api_key`, `jwt`, and `authorization` headers.
  - Sanitizes user input dictionaries and query parameters.
- **Performance Tracing**: Samples 10% of production transactions to trace slow database queries.

---

## 3. Deep Health Probes (`/health`)

Unlike shallow health checks that only verify the web server is responding, ShopZone executes **deep dependency probes**:

```python
@app.get("/health")
def health(strict: bool = False) -> JSONResponse:
    # 1. Probes PostgreSQL with SELECT 1
    # 2. Probes Redis with PING
    # 3. Gathers SQLAlchemy QueuePool checked-in / checked-out metrics
    # Returns HTTP 200 when operational, HTTP 503 when critical services are down
```

### Sample Health Payload:
```json
{
  "status": "ok",
  "service": "shopzone-api",
  "version": "1.0.0",
  "environment": "production",
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

---

## 4. Prometheus Metrics Exposition (`/metrics`)

Exposes standard Prometheus exposition format text for Prometheus servers, Grafana agents, or AWS CloudWatch Container Insights:
- `http_requests_total{method="GET",handler="/products",status="200"}`
- `http_request_duration_seconds_bucket{le="0.05"}`
- `shopzone_app_info{version="1.0.0",environment="production"}`

---

## 5. Uptime Monitoring Configuration (UptimeRobot)

An automated heartbeat probe is configured in UptimeRobot:
- **Monitored URL**: `https://day9-fastapi.vercel.app/api/health`
- **Probe Interval**: Every 60 seconds (1 minute)
- **HTTP Method**: `GET`
- **Expected Status Code**: `200`
- **Keyword Match**: `"status":"ok"`
- **Alert Escalation**:
  - Failure threshold: 2 consecutive missed heartbeats (2 minutes).
  - Notification channels: Email, Slack webhook, and SMS notification to on-call engineer.
