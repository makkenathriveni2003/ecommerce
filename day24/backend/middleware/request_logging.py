"""
Request Correlation & Logging Middleware for ShopZone FastAPI.
Assigns or forwards X-Request-ID headers, tracks request latency,
records Prometheus metrics, and outputs structured JSON logs.
"""

import logging
import time
import uuid
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import Response

from ..core.logging_config import request_id_var
from ..core.metrics import record_request_metrics

logger = logging.getLogger("shopzone.access")


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """
    Middleware that captures request duration, binds correlation IDs,
    records Prometheus metrics, and outputs structured logs.
    """

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        # Extract existing incoming X-Request-ID or generate new unique UUID
        req_id = request.headers.get("x-request-id") or request.headers.get("x-correlation-id") or uuid.uuid4().hex
        token = request_id_var.set(req_id)
        request.state.request_id = req_id

        start_time = time.perf_counter()
        status_code = 500

        try:
            response = await call_next(request)
            status_code = response.status_code
            response.headers["X-Request-ID"] = req_id
            return response
        except Exception:
            status_code = 500
            raise
        finally:
            duration = time.perf_counter() - start_time
            duration_ms = round(duration * 1000, 2)
            path = request.url.path

            # Record Prometheus metrics
            try:
                record_request_metrics(
                    method=request.method,
                    endpoint=path,
                    status_code=status_code,
                    duration_seconds=duration,
                )
            except Exception:
                pass

            # Structured access log entry
            log_data = {
                "method": request.method,
                "path": path,
                "status_code": status_code,
                "duration_ms": duration_ms,
                "client_ip": request.client.host if request.client else "unknown",
            }

            # Avoid log spam for frequent automated liveness/metric probes
            if path in ("/health", "/metrics", "/"):
                logger.debug("Probed %s - %s (%sms)", path, status_code, duration_ms, extra=log_data)
            elif status_code >= 500:
                logger.error("%s %s -> %s in %sms", request.method, path, status_code, duration_ms, extra=log_data)
            elif status_code >= 400:
                logger.warning("%s %s -> %s in %sms", request.method, path, status_code, duration_ms, extra=log_data)
            else:
                logger.info("%s %s -> %s in %sms", request.method, path, status_code, duration_ms, extra=log_data)

            request_id_var.reset(token)
