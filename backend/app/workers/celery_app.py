"""Celery application configuration."""

from celery import Celery
from celery.schedules import crontab

from app.core.config import settings

# Create Celery app
celery_app = Celery(
    "emailagent",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL,
    include=["app.workers.tasks"],
)

# Celery configuration
celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=600,  # 10 minutes max per task
    task_soft_time_limit=540,  # 9 minutes soft limit
    worker_prefetch_multiplier=1,
    worker_max_tasks_per_child=1000,
)

# Periodic tasks (Celery Beat schedule)
celery_app.conf.beat_schedule = {
    # Poll Gmail every 10 minutes
    "poll-gmail-every-10-minutes": {
        "task": "app.workers.tasks.poll_gmail_task",
        "schedule": 600.0,  # 10 minutes in seconds
    },
    # Run batch processing every 5 minutes (checks if within batch window)
    "check-batch-windows-every-5-minutes": {
        "task": "app.workers.tasks.run_email_batch",
        "schedule": 300.0,  # 5 minutes
    },
}


@celery_app.task(bind=True)
def debug_task(self):
    """Debug task to test Celery setup."""
    print(f"Request: {self.request!r}")
    return {"status": "ok"}
