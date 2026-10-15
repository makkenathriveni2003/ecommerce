import logging
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from slowapi.errors import RateLimitExceeded
from starlette.exceptions import HTTPException as StarletteHTTPException
from starlette.requests import Request
from starlette.responses import JSONResponse

from .core.config import settings
from .core.logging_config import setup_structured_logging
from .core.metrics import get_metrics_response, initialize_metrics
from .core.rate_limit import limiter, rate_limit_exceeded_handler
from .core.security import validate_token_configuration
from .core.sentry import init_sentry
from .db.database import database_connection, initialize_database
from .middleware.compression import setup_compression
from .middleware.request_logging import RequestLoggingMiddleware
from .middleware.security_headers import SecurityHeadersMiddleware

from .api.routers import admin, ai, auth, chat, orders, products, tasks, websocket

# Initialize structured JSON logging with level from configuration
setup_structured_logging(level=settings.LOG_LEVEL, service_name="shopzone-api")
logger = logging.getLogger("shopzone_api")


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    validate_token_configuration()
    initialize_database()
    app.state.database_ready = True

    # Initialize Sentry exception tracking (optional if SENTRY_DSN configured)
    init_sentry(
        dsn=settings.SENTRY_DSN,
        environment=settings.ENVIRONMENT,
        release=f"shopzone-backend@{settings.VERSION}",
    )

    # Initialize Prometheus metadata gauge
    initialize_metrics(
        version=settings.VERSION,
        environment=settings.ENVIRONMENT,
        service="shopzone-api",
    )

    # Seed ChromaDB vector store if empty
    try:
        from .services.ai import CatalogIndexer, ChromaVectorStore
        store = ChromaVectorStore()
        if store.count() == 0:
            logger.info("ChromaDB vector store is empty on startup. Indexing catalogue...")
            CatalogIndexer(vector_store=store).reindex_all_products(clear_existing=False)
    except Exception as init_ai_err:
        logger.warning("ChromaDB initial catalog indexing deferred: %s", init_ai_err)

    yield


app = FastAPI(
    title="GenZ Zone E-Commerce API",
    description="High-performance, AI-enhanced e-commerce REST & WebSocket API with Celery background processing and Redis caching",
    version=settings.VERSION,
    lifespan=lifespan,
)

# 1. SlowAPI Rate Limiting Setup
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, rate_limit_exceeded_handler)

# 2. CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_origin_regex=r"https?://.*",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 3. Security Headers Middleware
app.add_middleware(SecurityHeadersMiddleware)

# 4. GZip Response Compression Middleware
setup_compression(app, minimum_size=settings.GZIP_MINIMUM_SIZE)

# 5. Request Correlation & Metrics Middleware (outermost wrapper for end-to-end timing)
app.add_middleware(RequestLoggingMiddleware)


# 5. Global Exception Handlers
@app.exception_handler(StarletteHTTPException)
async def custom_http_exception_handler(request: Request, exc: StarletteHTTPException):
    origin = request.headers.get("origin") or "*"
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail},
        headers={
            "Access-Control-Allow-Origin": origin,
            "Access-Control-Allow-Credentials": "true",
            "Access-Control-Allow-Methods": "*",
            "Access-Control-Allow-Headers": "*",
        },
    )


@app.exception_handler(Exception)
async def custom_general_exception_handler(request: Request, exc: Exception):
    logger.exception("Internal server error: %s", exc)
    err_msg = str(exc).lower()
    origin = request.headers.get("origin") or "*"
    if "unique" in err_msg or "already exists" in err_msg or "duplicate key" in err_msg:
        return JSONResponse(
            status_code=409,
            content={"detail": "Email already registered. Please sign in instead."},
            headers={
                "Access-Control-Allow-Origin": origin,
                "Access-Control-Allow-Credentials": "true",
                "Access-Control-Allow-Methods": "*",
                "Access-Control-Allow-Headers": "*",
            },
        )
    return JSONResponse(
        status_code=500,
        content={"detail": "The server encountered a problem. Please try again."},
        headers={
            "Access-Control-Allow-Origin": origin,
            "Access-Control-Allow-Credentials": "true",
            "Access-Control-Allow-Methods": "*",
            "Access-Control-Allow-Headers": "*",
        },
    )


# 6. Register Subrouters (Direct and /api prefixed for unified Vercel multi-service routing)
app.include_router(auth.router)
app.include_router(products.router)
app.include_router(orders.router)
app.include_router(admin.router)
app.include_router(tasks.router)
app.include_router(chat.router)
app.include_router(websocket.router)
app.include_router(ai.router)

# Prefix aliases for single-domain routing
app.include_router(auth.router, prefix="/api")
app.include_router(products.router, prefix="/api")
app.include_router(orders.router, prefix="/api")
app.include_router(admin.router, prefix="/api")
app.include_router(tasks.router, prefix="/api")
app.include_router(chat.router, prefix="/api")
app.include_router(ai.router, prefix="/api")


@app.get("/")
def home() -> dict[str, str]:
    return {"message": "GenZ Zone E-Commerce Backend Running", "version": settings.VERSION}


@app.get("/health")
def health(strict: bool = False) -> JSONResponse:
    """
    Application Health Check.
    Probes core database and caching infrastructure without leaking internal credentials.
    """
    db_ok = False
    try:
        with database_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT 1")
                cur.fetchone()
        db_ok = True
    except Exception as db_err:
        logger.warning("Database health probe failed: %s", db_err)

    redis_ok = False
    try:
        import redis
        client = redis.from_url(settings.CELERY_BROKER_URL, socket_connect_timeout=1, socket_timeout=1)
        redis_ok = bool(client.ping())
    except Exception as redis_err:
        logger.debug("Redis health probe failed: %s", redis_err)

    components = {
        "database": "healthy" if db_ok else "unhealthy",
        "redis": "healthy" if redis_ok else "unhealthy",
    }

    is_healthy = (db_ok and redis_ok) if strict else db_ok
    status_code = 200 if is_healthy else 503

    return JSONResponse(
        status_code=status_code,
        content={
            "status": "ok" if (db_ok and redis_ok) else ("degraded" if db_ok else "unhealthy"),
            "service": "shopzone-api",
            "version": settings.VERSION,
            "environment": settings.ENVIRONMENT,
            "components": components,
        },
    )


@app.get("/metrics", include_in_schema=False)
def metrics():
    """Prometheus Scrape Endpoint."""
    return get_metrics_response()

