from celery import Celery
from app.config import settings

celery_app = Celery(
    "quantum_pharmx_tasks",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=3600, # 1 hour max for long jobs
)

# Autodiscover tasks from the workers package
celery_app.autodiscover_tasks(["app.workers"])
