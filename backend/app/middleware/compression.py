from fastapi import FastAPI
from fastapi.middleware.gzip import GZipMiddleware
from ..core.config import settings

def setup_compression(app: FastAPI, minimum_size: int = settings.GZIP_MINIMUM_SIZE) -> None:
    """
    Configures GZip response compression for responses larger than minimum_size bytes.
    Avoids compressing small payloads where compression overhead exceeds bandwidth gains.
    """
    app.add_middleware(GZipMiddleware, minimum_size=minimum_size)
