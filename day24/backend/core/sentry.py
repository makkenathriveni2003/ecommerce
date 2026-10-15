"""
Sentry Exception Tracking & Performance Monitoring Configuration.
Provides graceful initialization, sensitive data scrubbing (PII redaction),
and optional operation when SENTRY_DSN is not configured.
"""

import logging
from typing import Any, Dict, Optional
import sentry_sdk

logger = logging.getLogger("shopzone.sentry")

# Sensitive header keys to remove before sending to Sentry
SENSITIVE_HEADERS = {"authorization", "cookie", "set-cookie", "x-api-key"}


def before_send_filter(event: Dict[str, Any], hint: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """
    Scrub credentials, tokens, and authorization headers before sending error events to Sentry.
    """
    try:
        # Scrub request headers
        request = event.get("request", {})
        if "headers" in request and isinstance(request["headers"], dict):
            for header in list(request["headers"].keys()):
                if header.lower() in SENSITIVE_HEADERS:
                    request["headers"][header] = "[FILTERED]"

        # Scrub request body / query string if present
        if "data" in request:
            if isinstance(request["data"], dict):
                for k in list(request["data"].keys()):
                    if any(s in k.lower() for s in ("password", "token", "secret", "key")):
                        request["data"][k] = "[FILTERED]"

        # Remove local variables that might contain passwords from stack frames
        threads = event.get("threads", {}).get("values", [])
        for thread in threads:
            for frame in thread.get("stacktrace", {}).get("frames", []):
                vars_dict = frame.get("vars")
                if isinstance(vars_dict, dict):
                    for var_name in list(vars_dict.keys()):
                        if any(s in var_name.lower() for s in ("password", "secret", "token", "key")):
                            vars_dict[var_name] = "[FILTERED]"
    except Exception as scrub_err:
        logger.debug("Error during Sentry event sanitization: %s", scrub_err)

    return event


def init_sentry(
    dsn: str,
    environment: str = "development",
    release: str = "shopzone-backend@1.0.0",
    traces_sample_rate: float = 0.2,
) -> bool:
    """
    Initialize Sentry SDK if DSN is configured.
    Returns True if initialized, False if disabled.
    """
    cleaned_dsn = (dsn or "").strip()
    if not cleaned_dsn:
        logger.info("Sentry DSN is empty. Sentry exception tracking is disabled.")
        return False

    try:
        sentry_sdk.init(
            dsn=cleaned_dsn,
            environment=environment,
            release=release,
            traces_sample_rate=traces_sample_rate if environment == "production" else 1.0,
            send_default_pii=False,
            before_send=before_send_filter,
        )
        logger.info("Sentry initialized successfully (environment=%s, release=%s)", environment, release)
        return True
    except Exception as exc:
        logger.error("Failed to initialize Sentry SDK: %s", exc)
        return False
