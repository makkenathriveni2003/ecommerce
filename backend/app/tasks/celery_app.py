import os
import sys
from pathlib import Path

backend_dir = str(Path(__file__).resolve().parent.parent.parent)
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

from ..core.config import settings

# Ensure Redis 5 compatibility on Windows with RESP2 protocol
import redis.connection
try:
    from redis.maint_notifications import MaintNotificationsConfig
    redis.connection.DEFAULT_RESP_VERSION = 2
    orig_maint_init = MaintNotificationsConfig.__init__
    def _patched_maint_init(self, enabled=False, *args, **kwargs):
        orig_maint_init(self, enabled=enabled, *args, **kwargs)
    MaintNotificationsConfig.__init__ = _patched_maint_init
except Exception:
    pass

from celery import Celery

broker_url = settings.CELERY_BROKER_URL
result_backend = settings.CELERY_RESULT_BACKEND

if "protocol=" in broker_url:
    broker_url = broker_url.split("?")[0]
if "protocol=" in result_backend:
    result_backend = result_backend.split("?")[0]

celery_app = Celery(
    "shopzone_tasks",
    broker=broker_url,
    backend=result_backend,
    include=["app.tasks.celery_tasks", "tasks"],
)

celery_app.conf.update(
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_acks_late=True,
    worker_prefetch_multiplier=1,
    broker_connection_retry_on_startup=True,
)

if __name__ == "__main__":
    celery_app.start()
