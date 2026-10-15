# Day 24 – Task 4: Structured Application Logging & Sentry Integration

This guide details the implementation of structured JSON logging, correlation IDs, PII redaction, and Sentry error tracking for the ShopZone backend and frontend.

---

## 1. Structured Logging Architecture

Traditional text-based logs (`logger.info("Order 123 placed by alice")`) are difficult to query, filter, and alert on at scale in systems like AWS CloudWatch, Datadog, or Elasticsearch.

In Day 24, we implemented **Structured JSON Logging** with contextual correlation IDs via `backend/app/core/logging_config.py` and `backend/app/middleware/request_logging.py`.

### Structured Log Record Format

Every log output is emitted as a single-line JSON string:

```json
{
  "timestamp": "2026-10-15T12:30:19.735953+00:00",
  "level": "INFO",
  "service": "shopzone-api",
  "module": "shopzone.access",
  "message": "GET /api/products -> 200 in 12.4ms",
  "request_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "method": "GET",
  "path": "/api/products",
  "status_code": 200,
  "duration_ms": 12.4,
  "client_ip": "203.0.113.19"
}
```

### Key Capabilities:
1. **Timestamp:** High-precision ISO-8601 UTC timestamp.
2. **Correlation ID (`request_id`):** Propagated using Python's `contextvars.ContextVar`. Every log message emitted during a request lifecycle automatically includes the same ID.
3. **Response Header (`X-Request-ID`):** Returned to the client so customer-reported issues can be correlated directly with backend logs.
4. **PII & Credential Scrubbing:** Passwords, API keys, and authorization bearer tokens are automatically replaced with `[FILTERED]` before emission.

---

## 2. Sensitive Data & PII Redaction Rules

The logging formatter enforces redaction across both strings and dictionary payloads:

- **Redacted Header Values:** `Authorization`, `Cookie`, `Set-Cookie`, `X-Api-Key`
- **Redacted Keys in Dictionaries:** `password`, `token`, `secret`, `jwt_secret_key`, `access_token`, `refresh_token`, `credit_card`
- **Pattern Matchers:** Automatically filters strings matching `Bearer <token>` and `password=<value>`

---

## 3. Sentry Integration Setup

Sentry provides real-time exception tracking, stack traces, release monitoring, and performance telemetry.

### Step 3.1: Obtain your Sentry DSNs
1. Go to [sentry.io](https://sentry.io) and create a free developer account.
2. Create a project for **FastAPI (Python)**. Copy the DSN:
   `https://publicKey@o0.ingest.sentry.io/project-id`
3. Create a project for **React (JavaScript)**. Copy the DSN:
   `https://publicKey@o0.ingest.sentry.io/project-id-frontend`

### Step 3.2: Configure Environment Variables

**Backend (`.env` on EC2):**
```ini
ENVIRONMENT=production
SENTRY_DSN=https://publicKey@o0.ingest.sentry.io/project-id
```

**Frontend (Vercel Project Settings):**
```ini
VITE_SENTRY_DSN=https://publicKey@o0.ingest.sentry.io/project-id-frontend
```

### Step 3.3: Graceful Degradation
If `SENTRY_DSN` is empty:
- The backend logs: `[Sentry] Sentry DSN is empty. Sentry exception tracking is disabled.`
- The frontend logs: `[Sentry] VITE_SENTRY_DSN is not configured; frontend error tracking disabled.`
- The application runs normally without throwing any errors or crashing.

---

## 4. Testing Sentry Exception Capture

### Backend Test:
Trigger a test exception via Python terminal:
```bash
python -c "import sentry_sdk; sentry_sdk.init('YOUR_DSN'); sentry_sdk.capture_message('DevOps Day 24 Sentry Test')"
```
Inspect your Sentry dashboard to verify the alert appears within seconds.
