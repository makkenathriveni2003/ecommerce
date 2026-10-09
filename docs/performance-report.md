# ShopZone Performance & Optimization Report

## 1. Executive Summary

This report documents the performance optimizations, bundle analysis, compression metrics, automated load tests, and Lighthouse audit results for the ShopZone e-commerce application.

---

## 2. Frontend Bundle & Asset Optimization

### 2.1 Tooling & Code Splitting
- **Bundler:** Vite 8.3.2 with Rollup code-splitting configuration.
- **Vendor Splitting:** Configured chunk segregation in `frontend/vite.config.ts`:
  - `vendor-react` (React 19, ReactDOM)
  - `vendor-router` (React Router DOM v7)
  - `vendor-query` (TanStack Query v5)

### 2.2 Production Chunk Metrics
Production build output generated in **386ms**:

| Asset / Chunk | Raw Size | GZipped Size | Role |
| :--- | :--- | :--- | :--- |
| `index.html` | 31.28 kB | 7.28 kB | Entry HTML with preconnects |
| `index.css` | 30.21 kB | 6.78 kB | Consolidated app stylesheet |
| `index-BnnsXXdp.js` | **36.90 kB** | **12.20 kB** | **Core application bundle** (shrunk from 313 kB) |
| `vendor-query.js` | 37.57 kB | 11.77 kB | Cached TanStack Query library |
| `vendor-router.js` | 39.66 kB | 14.30 kB | Cached client routing library |
| `vendor-react.js` | 210.62 kB | 65.69 kB | Core UI runtime |
| `Checkout.js` | 116.71 kB | 35.67 kB | Lazy route (loaded only on checkout) |
| `AdminDashboard.js`| 15.30 kB | 4.65 kB | Lazy route (loaded only for admins) |
| `BackgroundJobs.js` | 9.87 kB | 2.76 kB | Lazy route (loaded on demand) |
| `OrderHistory.js` | 6.45 kB | 2.36 kB | Lazy route (loaded on demand) |
| `Cart.js` | 3.44 kB | 1.21 kB | Lazy route (loaded on demand) |
| `ProductDetails.js`| 1.31 kB | 0.61 kB | Lazy route (loaded on demand) |

### 2.3 Image Optimization & Delivery
- **Sanitized URL Construction:** Stripped duplicated query strings and applied format conversion (`?auto=format&fit=crop&w={width}&q=60`).
- **Payload Reduction:** Measured Unsplash thumbnail response size:
  - Unoptimized: `1,156,537 bytes` (1.15 MB)
  - Optimized: `19,780 bytes` (19.8 KB)
  - **Savings:** **98.3% payload reduction** per product card image.
- **Attributes:** Responsive `srcSet`, `sizes`, `loading="lazy"`, `decoding="async"`, and `fetchpriority="high"` for the above-the-fold hero item.

---

## 3. Response Compression (GZip)

- Configured FastAPI `GZipMiddleware` with `minimum_size=1000` via pure ASGI composition.
- **Verification:**
  - Small payloads (< 1000 bytes, e.g. `/health`, single item updates): Sent raw without GZip wrapping overhead (`Content-Encoding` absent).
  - Large payloads (>= 1000 bytes, e.g. `/products` 13-item catalog): Compressed with `Content-Encoding: gzip` when client sends `Accept-Encoding: gzip`.
  - Content integrity preserved across JSON serialization.

---

## 4. Google Lighthouse Audit Results

Audit executed using **Lighthouse CLI 13.5.0** and Headless Chrome against the production preview server (`http://127.0.0.1:4173`):

### Category Scores

| Category | Score | Status |
| :--- | :--- | :--- |
| **Performance** | **97 / 100** | **PASSED** (Exceeds 94-95 minimum requirement) |
| **Accessibility** | **100 / 100** | **PERFECT** |
| **Best Practices** | **100 / 100** | **PERFECT** |
| **SEO** | **100 / 100** | **PERFECT** |

### Core Web Vitals & Loading Metrics

| Metric | Measured Value | Audit Score |
| :--- | :--- | :--- |
| **First Contentful Paint (FCP)** | 1.7 s | 0.91 |
| **Largest Contentful Paint (LCP)** | 2.4 s | 0.91 |
| **Total Blocking Time (TBT)** | 40 ms | 1.00 (Perfect) |
| **Cumulative Layout Shift (CLS)** | 0.001 | 1.00 (Perfect) |
| **Speed Index** | 1.7 s | 1.00 (Perfect) |

---

## 5. Locust Load Testing (50 Concurrent Users)

### Test Configuration
- **Script:** `loadtests/locustfile.py`
- **User Population:** 50 concurrent simulated shoppers (pre-authenticated JWT users and anonymous catalog visitors)
- **Ramp-up / Spawn Rate:** 10 users per second
- **Duration:** 20 seconds headless test
- **Target Host:** `http://127.0.0.1:8000`

### Aggregate Results

| Metric | Measured Result |
| :--- | :--- |
| **Total Requests Executed** | 695 |
| **Total Failures** | **0 (0.00%)** |
| **Throughput (Requests/sec)** | **34.27 RPS** |
| **Median Response Time (p50)** | **86 ms** |
| **Average Response Time** | **105 ms** |
| **90th Percentile (p90)** | **180 ms** |
| **95th Percentile (p95)** | **240 ms** |
| **99th Percentile (p99)** | **350 ms** |

### Endpoint Breakdown

| Endpoint / Scenario | Requests | Failures | Median | Average | p95 | RPS |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `GET / [Root Health]` | 36 | 0 (0%) | 6 ms | 7 ms | 13 ms | 1.78 |
| `GET /orders/optimized [SQLAlchemy Eager]` | 116 | 0 (0%) | 90 ms | 105 ms | 190 ms | 5.72 |
| `GET /orders [Raw History]` | 64 | 0 (0%) | 180 ms | 185 ms | 350 ms | 3.16 |
| `GET /products [Catalog]` | 172 | 0 (0%) | 84 ms | 107 ms | 240 ms | 8.48 |
| `GET /products/search [FTS & Fuzzy]` | 170 | 0 (0%) | 87 ms | 106 ms | 200 ms | 8.38 |
| `GET /products/{id} [Details]` | 137 | 0 (0%) | 76 ms | 91 ms | 180 ms | 6.76 |

### Architectural Insight: Eager Loading Optimization
Under 50 concurrent users:
- `/orders` (lazy N+1 queries) required **180 ms median** and **350 ms p95**.
- `/orders/optimized` (SQLAlchemy `selectinload` / `joinedload`) achieved **90 ms median** and **190 ms p95**.
- Result: **50% latency reduction** under active load through database query optimization.
