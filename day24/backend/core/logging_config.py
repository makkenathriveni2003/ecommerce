"""
Structured Logging & PII Sanitization for ShopZone FastAPI Backend.
Formats application logs into structured JSON suitable for AWS CloudWatch and container logging,
with automatic request ID correlation and redaction of sensitive credentials and tokens.
"""

import contextvars
import datetime
import json
import logging
import re
import sys
from typing import Any, Dict, Optional

# Context variable to hold request correlation ID across async tasks
request_id_var: contextvars.ContextVar[str] = contextvars.ContextVar("request_id", default="")

# Sensitive key patterns to redact in logged metadata or messages
SENSITIVE_KEYS = {
    "password",
    "passwd",
    "secret",
    "token",
    "access_token",
    "refresh_token",
    "authorization",
    "jwt_secret_key",
    "api_key",
    "groq_api_key",
    "gemini_api_key",
    "mistral_api_key",
    "openai_api_key",
    "sentry_dsn",
    "postgres_password",
    "redis_password",
}

# Regex to scrub bearer tokens and passwords in raw strings
BEARER_REGEX = re.compile(r"Bearer\s+[A-Za-z0-9\-_.]+", re.IGNORECASE)
PASSWORD_QUOTED_REGEX = re.compile(r'((?:password|passwd|token|secret|key)["\']?\s*[:=]\s*["\'])([^"\']+)(["\'])', re.IGNORECASE)
PASSWORD_UNQUOTED_REGEX = re.compile(r'((?:password|passwd|token|secret|key)\s*[:=]\s*)([^\s,"\'&]+)', re.IGNORECASE)


def sanitize_text(text: str) -> str:
    """Scrub sensitive credentials, passwords, and bearer tokens from a log string."""
    if not isinstance(text, str):
        return text
    scrubbed = BEARER_REGEX.sub("Bearer [FILTERED]", text)
    scrubbed = PASSWORD_QUOTED_REGEX.sub(r"\1[FILTERED]\3", scrubbed)
    scrubbed = PASSWORD_UNQUOTED_REGEX.sub(r"\1[FILTERED]", scrubbed)
    return scrubbed


def sanitize_data(data: Any) -> Any:
    """Recursively scrub sensitive keys and tokens from dict/list structures."""
    if isinstance(data, dict):
        clean: Dict[str, Any] = {}
        for k, v in data.items():
            if str(k).lower() in SENSITIVE_KEYS or any(s in str(k).lower() for s in ("password", "secret", "token")):
                clean[k] = "[FILTERED]"
            else:
                clean[k] = sanitize_data(v)
        return clean
    elif isinstance(data, list):
        return [sanitize_data(item) for item in data]
    elif isinstance(data, str):
        return sanitize_text(data)
    return data


class StructuredJsonFormatter(logging.Formatter):
    """
    JSON Formatter for CloudWatch and production observability.
    Produces one valid JSON object per log record with standardized fields.
    """

    def __init__(self, service_name: str = "shopzone-api"):
        super().__init__()
        self.service_name = service_name

    def format(self, record: logging.LogRecord) -> str:
        req_id = request_id_var.get("")
        if not req_id and hasattr(record, "request_id"):
            req_id = getattr(record, "request_id")

        timestamp = datetime.datetime.fromtimestamp(record.created, datetime.timezone.utc).isoformat()

        # Base structured fields
        log_entry: Dict[str, Any] = {
            "timestamp": timestamp,
            "level": record.levelname,
            "service": self.service_name,
            "module": record.name,
            "message": sanitize_text(record.getMessage()),
        }

        if req_id:
            log_entry["request_id"] = req_id

        # Optional HTTP metadata attached to the record
        for field in ("method", "path", "status_code", "duration_ms", "client_ip", "user_agent"):
            if hasattr(record, field):
                log_entry[field] = getattr(record, field)

        # Exception stack trace if present
        if record.exc_info:
            log_entry["exception"] = self.formatException(record.exc_info)
        elif record.exc_text:
            log_entry["exception"] = record.exc_text

        # Extra metadata if provided
        if hasattr(record, "extra_data") and isinstance(record.extra_data, dict):
            log_entry["data"] = sanitize_data(record.extra_data)

        return json.dumps(log_entry, default=str)


def setup_structured_logging(
    level: str = "INFO",
    service_name: str = "shopzone-api",
    force_json: bool = True,
) -> None:
    """
    Initialize root and application loggers with structured formatting.
    """
    log_level = getattr(logging, level.upper(), logging.INFO)
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)

    # Remove existing handlers to avoid duplicate log entries
    for handler in list(root_logger.handlers):
        root_logger.removeHandler(handler)

    stream_handler = logging.StreamHandler(sys.stdout)
    stream_handler.setLevel(log_level)
    stream_handler.setFormatter(StructuredJsonFormatter(service_name=service_name))
    root_logger.addHandler(stream_handler)

    # Adjust external noisy libraries
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("passlib").setLevel(logging.WARNING)
    logging.getLogger("chromadb").setLevel(logging.WARNING)
