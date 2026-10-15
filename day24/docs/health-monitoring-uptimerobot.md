# Day 24 – Task 5: Health Checks, Prometheus Metrics & UptimeRobot Monitoring

This guide covers the health-check design, Prometheus metrics collection, and external uptime monitoring for the ShopZone platform.

---

## 1. Backend Health Check Architecture (`/health`)

A naive health check returns `200 OK` without checking whether internal dependencies are functioning. If the database crashes, a naive health check reports healthy while users experience 500 errors.

In Day 24, the `/health` endpoint performs a **shallow component verification**:

```
           GET /health
                │
                ├── 1. Query DB: "SELECT 1" (timeout 1s)
                │      └── Pass / Fail
                │
                ├── 2. Ping Redis: "PING" (timeout 1s)
                │      └── Pass / Fail
                │
                ▼
       Evaluates Status:
       • If all healthy -> 200 OK {"status": "ok", ...}
       • If DB fails    -> 503 Service Unavailable {"status": "unhealthy", ...}
```

### Sample Response:
```json
{
  "status": "ok",
  "service": "shopzone-api",
  "version": "1.0.0",
  "environment": "production",
  "components": {
    "database": "healthy",
    "redis": "healthy"
  }
}
```

> [!SECURITY]
> The health check **never exposes internal database connection strings, passwords, server hostnames, or raw error stack traces**. Only high-level component health flags (`healthy` / `unhealthy`) are returned.

---

## 2. Prometheus Metrics (`/metrics`)

Operational metrics are emitted in the standard Prometheus exposition format at `/metrics`:

### Exposed Metrics:

| Metric Name | Type | Labels | Description |
| :--- | :--- | :--- | :--- |
| `http_requests_total` | Counter | `method`, `endpoint`, `status_code` | Total HTTP request counter |
| `http_request_duration_seconds` | Histogram | `method`, `endpoint` | Request latency distribution across standard duration buckets |
| `http_errors_total` | Counter | `method`, `endpoint`, `error_type` | Count of 4xx client errors and 5xx server errors |
| `shopzone_app_info` | Gauge | `version`, `environment`, `service` | Build and deployment metadata |

### Sample Scraped Output:
```text
# HELP http_requests_total Total HTTP request count partitioned by method, endpoint, and status code
# TYPE http_requests_total counter
http_requests_total{endpoint="/api/products",method="GET",status_code="200"} 45.0
http_requests_total{endpoint="/api/orders",method="POST",status_code="201"} 12.0

# HELP http_request_duration_seconds HTTP request latency in seconds
# TYPE http_request_duration_seconds histogram
http_request_duration_seconds_bucket{endpoint="/api/products",le="0.05",method="GET"} 38.0
http_request_duration_seconds_count{endpoint="/api/products",method="GET"} 45.0
http_request_duration_seconds_sum{endpoint="/api/products",method="GET"} 1.254
```

---

## 3. Configuring UptimeRobot Availability Monitoring

UptimeRobot monitors public endpoints from global probe locations every 60 seconds and triggers immediate email or SMS alerts when downtime occurs.

### Step 3.1: Create Free UptimeRobot Account
Sign up at [uptimerobot.com](https://uptimerobot.com) (free tier includes 50 monitors checked every 5 minutes).

### Step 3.2: Add New Monitor for ShopZone
1. Click **+ Add New Monitor**.
2. **Monitor Type:** `HTTP(s)`
3. **Friendly Name:** `ShopZone Production API`
4. **URL (or IP):** `https://api.yourdomain.com/health` (or `http://<EC2_ELASTIC_IP>/health`)
5. **Monitoring Interval:** `1 minute` (or `5 minutes` on free plan)
6. **Monitor Timeout:** `30 seconds`
7. **HTTP Status Code Alert:** Triggers when status code is not in `200..299` (e.g. 503 or 500 triggers alert).
8. **Alert Contacts:** Select your email address.
9. Click **Create Monitor**.

### Step 3.3: Add Monitor for Vercel Frontend
1. Click **+ Add New Monitor**.
2. **Friendly Name:** `ShopZone Vercel Frontend`
3. **URL:** `https://your-shopzone.vercel.app`
4. **Monitoring Interval:** `5 minutes`
5. **Alert Contacts:** Select your email address.
