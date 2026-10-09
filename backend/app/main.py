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
from .core.rate_limit import limiter, rate_limit_exceeded_handler
from .core.security import validate_token_configuration
from .db.database import initialize_database
from .middleware.compression import setup_compression
from .middleware.security_headers import SecurityHeadersMiddleware

from .api.routers import admin, auth, chat, orders, products, tasks, websocket

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("shopzone_api")


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    validate_token_configuration()
    initialize_database()
    app.state.database_ready = True
    yield


app = FastAPI(
    title="ShopZone E-Commerce API",
    description="High-performance, secure e-commerce REST & WebSocket API with Celery background processing",
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


# 6. Register Subrouters
app.include_router(auth.router)
app.include_router(products.router)
app.include_router(orders.router)
app.include_router(admin.router)
app.include_router(tasks.router)
app.include_router(chat.router)
app.include_router(websocket.router)


@app.get("/")
def home() -> dict[str, str]:
    return {"message": "ShopZone E-Commerce Backend Running", "version": settings.VERSION}


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "service": "shopzone-api", "version": settings.VERSION}

