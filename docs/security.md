# ShopZone API Security & OWASP Top 10 Compliance Architecture

## 1. Executive Summary

The ShopZone application incorporates security best practices designed to address the **OWASP API Security Top 10 (2023)** risks. This document outlines the backend and frontend security controls, rate limiting architecture, authorization enforcement, and defensive middleware implemented in the system.

---

## 2. OWASP API Security Top 10 Mitigations

| OWASP Risk | Vulnerability Description | ShopZone Defensive Implementation |
| :--- | :--- | :--- |
| **API1:2023 Broken Object Level Authorization (BOLA / IDOR)** | Attackers manipulate resource identifiers to access data belonging to other users. | Enforced in `app/core/security.py` via `verify_object_ownership(resource_owner_id, current_user)`. Customers can only query, modify, or download their own orders and invoices; administrators have authorized global access. Unauthorized cross-tenant access returns HTTP 403 Forbidden. |
| **API2:2023 Broken Authentication** | Compromised credential handling, weak hashing, or vulnerable tokens. | Passwords hashed using PBKDF2-SHA256 with 600,000 iterations and salt. Tokens issued via HS256 JWT with strict expiration (`ACCESS_TOKEN_EXPIRE_MINUTES`). Endpoints validate Bearer tokens and verify user existence in PostgreSQL before granting context. |
| **API3:2023 Broken Object Property Level Authorization** | Exposure of sensitive internal fields or mass-assignment attacks. | Strict Pydantic response models (`response_model=schemas.UserResponse`, `schemas.ProductResponse`, `schemas.OrderResponse`). Sensitive fields such as `hashed_password` are excluded from all outgoing schemas. Request bodies are strictly typed with schemas like `ProductCreate`, preventing mass-assignment. |
| **API4:2023 Unrestricted Resource Consumption** | Denial-of-Service via unthrottled requests, unbounded queries, or large payloads. | SlowAPI rate limiting per client IP (with `X-Forwarded-For` proxy awareness). Configurable limits: `5/minute` for login, `3/minute` for registration, `10/minute` for sensitive endpoints. Pagination and bounded queries across all catalog searches. |
| **API5:2023 Broken Function Level Authorization (BFLA / RBAC)** | Regular users executing administrative tasks (e.g., product creation, bulk CSV imports). | Enforced using FastAPI dependency `require_admin`. Routes such as `POST /products`, `DELETE /products/{id}`, and `POST /tasks/bulk-import` verify `current_user.role == "admin"`. Non-admin users receive HTTP 403 Forbidden. |
| **API6:2023 Unrestricted Access to Sensitive Business Flows** | Automated bots abusing checkout or invoice generation. | Authenticated checkout workflow validating real-time product inventory inside a single atomic database transaction. Celery task dispatch rate limits for PDF invoice generation and bulk CSV imports. |
| **API7:2023 Server-Side Request Forgery (SSRF)** | Exploitation of server requests to untrusted external URLs. | ShopZone restricts external asset references to trusted CDNs (e.g., Unsplash) via Content Security Policy headers. File uploads and bulk CSV imports process files from memory or bounded temporary storage without executing external web hooks. |
| **API8:2023 Security Misconfiguration** | Missing security headers, exposed stack traces, or permissive CORS. | `SecurityHeadersMiddleware` injects OWASP headers on every response (`X-Content-Type-Options: nosniff`, `X-Frame-Options: DENY`, `Content-Security-Policy`, `Referrer-Policy`). Production CORS restricts allowed origins. Unhandled exceptions return generic 500 JSON envelopes rather than raw Python tracebacks. |
| **API9:2023 Improper Inventory Management** | Undocumented or legacy API versions exposed without authorization. | OpenAPI / Swagger documentation (`/docs`, `/redoc`) is maintained and reflects active versioned routes. Legacy endpoints use backward-compatibility proxy shims that inherit the same security dependencies and rate limits. |
| **API10:2023 Unsafe Consumption of APIs** | Blindly trusting inputs from third-party services or background workers. | Background worker tasks (Celery) validate task payloads, parse CSVs with explicit schemas, and verify file boundaries before saving records to PostgreSQL. |

---

## 3. SlowAPI Rate Limiting Architecture

Rate limiting is orchestrated via SlowAPI in `backend/app/core/rate_limit.py`.

### Client IP Extraction
To function reliably in production environments behind reverse proxies (Nginx, Cloudflare, Traefik, AWS ALB), client IP extraction prioritizes:
1. `X-Forwarded-For` header (taking the first client IP in the chain).
2. `X-Real-IP` header.
3. Fallback to `request.client.host`.

### Rate Limit Tiers

| Endpoint | Limit | Purpose |
| :--- | :--- | :--- |
| `POST /auth/login` | `5 per minute` | Prevents credential stuffing and brute-force attacks. |
| `POST /auth/register` | `3 per minute` | Prevents automated spam account creation. |
| `POST /tasks/sample-job` | `10 per minute` | Prevents background queue starvation. |
| Sensitive / Admin Endpoints | `10 per minute` | Protects privileged workflows. |
| General API Endpoints | `100 per minute` | Normal client traffic headroom. |

### 429 Too Many Requests Response
When limits are exceeded, SlowAPI invokes a custom JSON exception handler:
```json
{
  "detail": "Rate limit exceeded: 5 per 1 minute. Please retry after 58 seconds.",
  "retry_after": 58
}
```
The response includes the standard HTTP `Retry-After: 58` header.

---

## 4. Security Headers Middleware

Implemented as a high-performance pure ASGI middleware (`backend/app/middleware/security_headers.py`) to preserve response body chunking and GZip compatibility:

```http
X-Content-Type-Options: nosniff
X-Frame-Options: DENY
X-XSS-Protection: 1; mode=block
Referrer-Policy: strict-origin-when-cross-origin
Content-Security-Policy: default-src 'self'; img-src 'self' data: https:; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline'; connect-src 'self' ws: wss: http: https:;
```

---

## 5. Automated Security Test Verification

The backend automated test suite (`backend/tests/test_security.py` and `backend/tests/test_rate_limit.py`) exercises:
1. **Unauthorized Access:** Requests to protected endpoints without JWT tokens return HTTP 401.
2. **Forbidden Access (RBAC):** Customer attempts to create products return HTTP 403.
3. **BOLA / IDOR Verification:** User A querying User B's order details returns HTTP 403.
4. **Admin Override:** Admins querying customer orders return HTTP 200.
5. **Rate Limiting:** Bursting beyond endpoint thresholds triggers HTTP 429 with `Retry-After`.
6. **Input Validation:** Malformed or missing JSON bodies return HTTP 422 with structured field error descriptions.
