"""Celery application configuration."""
from celery import Celery

from app.core.config import settings

# Register all SQLAlchemy models so FK metadata resolves in workers
from app.users.models import User  # noqa: F401

celery_app = Celery(
    "fastapi_app",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND_URL,
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=30 * 60,  # 30 minutes hard limit
    task_soft_time_limit=25 * 60,  # 25 minutes soft limit
    worker_prefetch_multiplier=4,
    worker_max_tasks_per_child=1000,
    beat_scheduler="celery.beat:PersistentScheduler",
)

# Import and set Celery Beat schedule
from celery_beat_schedule import CELERY_BEAT_SCHEDULE
celery_app.conf.beat_schedule = CELERY_BEAT_SCHEDULE

# Auto-discover tasks from all registered apps
celery_app.autodiscover_tasks(["app"])
