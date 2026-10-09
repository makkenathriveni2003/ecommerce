# Day 19 – Complete ShopZone Full-Stack Project

Complete full-stack implementation of the **Day 19 ShopZone E-Commerce platform** featuring:
- **Backend Modular Architecture** (`app/core/`, `app/api/routers/`, `app/services/`, `app/models/`, `app/schemas/`, `app/middleware/`, `app/tasks/`)
- **OWASP API Security Top 10 Compliance** (BOLA/IDOR protection, RBAC, safe schemas, secure headers)
- **FastAPI Rate Limiting with SlowAPI** (Reverse-proxy IP extraction, burst limits on login, registration, and sensitive APIs)
- **FastAPI GZip Response Compression** (`minimum_size=1000` bytes)
- **Frontend Performance Optimization** (Vite 8 / Rollup manualChunks, 36.90 kB core bundle, 98.3% image payload reduction)
- **Google Lighthouse Audits** (Performance: **97/100**, Accessibility: **100/100**, Best Practices: **100/100**, SEO: **100/100**)
- **Locust Load Testing** (50 concurrent simulated users, 34.27 RPS, 86 ms median latency, 0% failure rate)
- **100% Automated Test Coverage** (47 Pytest tests passed, 83 Vitest tests passed)

---

## 1. Quick Start Commands

### Step 1: Start Redis
```powershell
.\redis\redis-server.exe .\redis\redis.windows.conf
```

### Step 2: Start Celery Background Worker
```powershell
py -3.14 -m celery -A backend.celery_app.celery_app worker --loglevel=info --pool=solo
```

### Step 3: Start FastAPI Backend
```powershell
py -3.14 -m uvicorn app.main:app --app-dir backend --port 8000
```

### Step 4: Start Frontend
```powershell
cd frontend
npm run dev
# or preview the optimized production build:
npm run preview -- --port 4173
```

---

## 2. Directory Structure

- `backend/app/`: Modular application source code (core, api, db, models, schemas, services, middleware, tasks).
- `backend/tests/`: Automated Pytest test suite for Day 19 features (auth, security, rate limit, products, orders, integration).
- `frontend/`: React 19 + TypeScript + Vite application with optimized manualChunks code-splitting.
- `loadtests/`: Locust load testing scenarios (`locustfile.py`) and Lighthouse reports.
- `docs/`: Complete project documentation:
  - `docs/setup.md`: System requirements and startup guide.
  - `docs/security.md`: OWASP Top 10 mitigations & SlowAPI configuration.
  - `docs/performance-report.md`: Lighthouse (97/100), bundle size, and Locust 50-user load tests.
  - `docs/final-demo.md`: Step-by-step verification script for all 12 workflows.
- `redis/`: Local Redis server binary & configuration.
- `test_data/`: Seed data and test CSV files.

---

## 3. Verification & Testing Commands

```powershell
# Run backend tests (47 passed)
py -3.14 -m pytest backend/tests/ tests_day18/ -v

# Run frontend tests (83 passed)
cd frontend
npm test

# Run Locust load test (50 users)
py -3.14 -m locust -f loadtests/locustfile.py --headless -u 50 -r 10 --run-time 20s --host http://127.0.0.1:8000

# Run Lighthouse audit
npx lighthouse http://127.0.0.1:4173 --chrome-flags="--headless=new --no-sandbox" --output=json --output-path=./loadtests/lighthouse-report.json --quiet
```
