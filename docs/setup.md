# ShopZone Full-Stack Setup Guide

This document describes how to set up, configure, and run the ShopZone e-commerce application across backend, database, cache, background workers, and frontend.

---

## 1. Prerequisites & Environment

- **Operating System:** Windows, Linux, or macOS
- **Python:** Python 3.12+ (tested on Python 3.14.7)
- **Node.js:** Node.js 20+ (tested on Node.js v24.21.0) with npm
- **Database:** PostgreSQL 14+ (tested on PostgreSQL with user `Thriveni` / database `sqlight`)
- **In-Memory Cache & Message Broker:** Redis 5.0+ (Windows binary included in `./redis/`)

---

## 2. Directory Architecture

```
day9-fastapi/
├── backend/
│   ├── app/
│   │   ├── main.py              # Application initialization, middleware, routes
│   │   ├── core/
│   │   │   ├── config.py        # Centralized Pydantic BaseSettings
│   │   │   ├── security.py      # JWT auth, password hashing, IDOR & RBAC guards
│   │   │   └── rate_limit.py    # SlowAPI rate limiter & 429 handler
│   │   ├── api/
│   │   │   └── routers/         # Auth, products, orders, admin, tasks, chat, ws
│   │   ├── db/
│   │   │   └── session.py       # SQLAlchemy engine, pool, sessionmaker
│   │   ├── models/              # SQLAlchemy ORM models
│   │   ├── schemas/             # Pydantic request & response schemas
│   │   ├── services/            # Business logic layer
│   │   ├── middleware/          # Security headers & compression
│   │   └── tasks/               # Celery worker & background tasks
│   ├── tests/                   # Pytest test suite (auth, security, rate limit, etc.)
│   ├── requirements.txt         # Python package dependencies
│   └── .env.example             # Template environment variables
├── frontend/
│   ├── src/                     # React 19 + TypeScript source
│   ├── package.json             # NPM dependencies & scripts
│   └── vite.config.ts           # Vite 8 config with Rollup manualChunks
├── loadtests/
│   └── locustfile.py            # Locust load test scenarios (up to 50 users)
├── docs/                        # Complete architecture & runbooks
└── redis/                       # Local Redis server binary & configuration
```

---

## 3. Backend Configuration

1. **Navigate to the Backend Directory:**
   ```powershell
   cd c:\Users\Dell\Downloads\day9-fastapi\backend
   ```

2. **Configure Environment Variables:**
   Create a `.env` file from `.env.example`:
   ```ini
   DATABASE_URL=postgresql://Thriveni:password@localhost:5432/sqlight
   REDIS_URL=redis://localhost:6379/0
   CELERY_BROKER_URL=redis://localhost:6379/0
   CELERY_RESULT_BACKEND=redis://localhost:6379/0
   SECRET_KEY=dev-secret-key-shopzone-day19-super-secure-token
   ALGORITHM=HS256
   ACCESS_TOKEN_EXPIRE_MINUTES=60
   ALLOWED_ORIGINS=http://localhost:5173,http://127.0.0.1:5173,http://localhost:4173,http://127.0.0.1:4173
   RATE_LIMIT_LOGIN=5/minute
   RATE_LIMIT_REGISTER=3/minute
   RATE_LIMIT_SENSITIVE=10/minute
   RATE_LIMIT_DEFAULT=100/minute
   GZIP_MINIMUM_SIZE=1000
   ```

3. **Install Dependencies:**
   ```powershell
   py -3.14 -m pip install -r requirements.txt
   ```

---

## 4. Starting Supporting Services

### Step A: Start Redis Cache & Message Broker
Open a PowerShell terminal and run:
```powershell
.\redis\redis-server.exe .\redis\redis.windows.conf
```
*Redis listens by default on `127.0.0.1:6379`.*

### Step B: Start Celery Background Worker
Open a second PowerShell terminal and run:
```powershell
py -3.14 -m celery -A backend.celery_app.celery_app worker --loglevel=info --pool=solo
```
*Note: `--pool=solo` is recommended on Windows.*

### Step C: Start FastAPI Application
Open a third PowerShell terminal and run:
```powershell
py -3.14 -m uvicorn app.main:app --app-dir backend --reload --port 8000
```
- Interactive API Docs (Swagger): `http://127.0.0.1:8000/docs`
- Alternative API Docs (ReDoc): `http://127.0.0.1:8000/redoc`
- Health check: `http://127.0.0.1:8000/health`

---

## 5. Starting the Frontend Application

1. **Navigate to the Frontend Directory:**
   ```powershell
   cd c:\Users\Dell\Downloads\day9-fastapi\frontend
   ```

2. **Install NPM Packages:**
   ```powershell
   npm install
   ```

3. **Development Mode:**
   ```powershell
   npm run dev
   ```
   *Serves application at `http://localhost:5173` with Hot Module Replacement (HMR).*

4. **Production Build & Preview:**
   ```powershell
   npm run build
   npm run preview -- --port 4173
   ```
   *Serves optimized production bundle at `http://localhost:4173`.*

---

## 6. Running Tests & Load Testing

### Run Backend Automated Tests
```powershell
py -3.14 -m pytest backend/tests/ -v
```

### Run Frontend Unit Tests
```powershell
cd frontend
npm test
```

### Run Locust Load Test (50 Concurrent Users)
```powershell
locust -f loadtests/locustfile.py --headless -u 50 -r 10 --run-time 30s --host http://127.0.0.1:8000
```
