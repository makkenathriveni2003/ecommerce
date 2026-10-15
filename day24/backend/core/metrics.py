"""
Prometheus Metrics Instrumentation for ShopZone FastAPI Backend.
Exposes standard operational metrics: request counts, duration histograms,
error counts, and application version metadata.
"""

from typing import Optional
from fastapi import Response
from prometheus_client import (
    CONTENT_TYPE_LATEST,
    Counter,
    Gauge,
    Histogram,
    generate_latest,
)

# Standard HTTP metrics
HTTP_REQUESTS_TOTAL = Counter(
    "http_requests_total",
    "Total HTTP request count partitioned by method, endpoint, and status code",
    ["method", "endpoint", "status_code"],
)

HTTP_REQUEST_DURATION_SECONDS = Histogram(
    "http_request_duration_seconds",
    "HTTP request latency in seconds",
    ["method", "endpoint"],
    buckets=(0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0),
)

HTTP_ERRORS_TOTAL = Counter(
    "http_errors_total",
    "Total count of HTTP 4xx client errors and 5xx server errors",
    ["method", "endpoint", "error_type"],
)

APP_INFO = Gauge(
    "shopzone_app_info",
    "Application metadata information",
    ["version", "environment", "service"],
)


def initialize_metrics(version: str = "1.0.0", environment: str = "development", service: str = "shopzone-api") -> None:
    """Initialize static metadata gauge."""
    try:
        APP_INFO.labels(version=version, environment=environment, service=service).set(1)
    except Exception:
        pass


def record_request_metrics(method: str, endpoint: str, status_code: int, duration_seconds: float) -> None:
    """Record metrics for a completed HTTP request."""
    clean_endpoint = endpoint
    # Collapse dynamic ID paths (e.g. /api/products/42 -> /api/products/{id})
    parts = endpoint.strip("/").split("/")
    if len(parts) >= 2 and parts[-1].isdigit():
        parts[-1] = "{id}"
        clean_endpoint = "/" + "/".join(parts)

    status_str = str(status_code)
    HTTP_REQUESTS_TOTAL.labels(method=method, endpoint=clean_endpoint, status_code=status_str).inc()
    HTTP_REQUEST_DURATION_SECONDS.labels(method=method, endpoint=clean_endpoint).observe(duration_seconds)

    if status_code >= 500:
        HTTP_ERRORS_TOTAL.labels(method=method, endpoint=clean_endpoint, error_type="server_error").inc()
    elif status_code >= 400:
        HTTP_ERRORS_TOTAL.labels(method=method, endpoint=clean_endpoint, error_type="client_error").inc()


def get_metrics_response() -> Response:
    """Generate Prometheus scrape format response."""
    return Response(
        content=generate_latest(),
        media_type=CONTENT_TYPE_LATEST,
        headers={"Cache-Control": "no-cache, no-store, must-revalidate"},
    )
