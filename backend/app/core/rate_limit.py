from starlette.requests import Request
from starlette.responses import JSONResponse
from slowapi import Limiter
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from .config import settings

def get_client_ip(request: Request) -> str:
    """Accurately extract client IP handling X-Forwarded-For or direct client host."""
    forwarded_for = request.headers.get("X-Forwarded-For")
    if forwarded_for:
        return forwarded_for.split(",")[0].strip()
    real_ip = request.headers.get("X-Real-IP")
    if real_ip:
        return real_ip.strip()
    return get_remote_address(request) or "127.0.0.1"


limiter = Limiter(
    key_func=get_client_ip,
    default_limits=[settings.DEFAULT_RATE_LIMIT] if settings.RATE_LIMIT_ENABLED else [],
    enabled=settings.RATE_LIMIT_ENABLED,
)


def rate_limit_exceeded_handler(request: Request, exc: RateLimitExceeded) -> JSONResponse:
    """Standardized JSON response for 429 Too Many Requests."""
    origin = request.headers.get("origin") or "*"
    retry_after = getattr(exc, "retry_after", 60)
    return JSONResponse(
        status_code=429,
        content={
            "error": "Rate limit exceeded",
            "detail": f"Too many requests. Limit exceeded: {exc.detail}. Please try again later.",
            "retry_after": retry_after,
        },
        headers={
            "Retry-After": str(retry_after),
            "Access-Control-Allow-Origin": origin,
            "Access-Control-Allow-Credentials": "true",
            "Access-Control-Allow-Methods": "*",
            "Access-Control-Allow-Headers": "*",
        },
    )
