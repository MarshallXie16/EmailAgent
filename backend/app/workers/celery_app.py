"""Celery application configuration."""

from celery import Celery
from celery.schedules import crontab
from celery.signals import task_prerun, task_postrun, task_failure

from app.core.config import settings
from app.core.logging_config import setup_logging, get_logger, set_request_context, clear_request_context

# Initialize structured logging for Celery workers
setup_logging(log_level=settings.LOG_LEVEL if hasattr(settings, "LOG_LEVEL") else "INFO")
logger = get_logger(__name__)

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


# Celery task logging signals
@task_prerun.connect
def task_prerun_handler(task_id, task, *args, **kwargs):
    """Log before task execution."""
    set_request_context(request_id=task_id)
    logger.info(
        "Celery task started",
        extra={
            "task_id": task_id,
            "task_name": task.name,
            "args": str(args),
        }
    )


@task_postrun.connect
def task_postrun_handler(task_id, task, retval, *args, **kwargs):
    """Log after task execution."""
    logger.info(
        "Celery task completed",
        extra={
            "task_id": task_id,
            "task_name": task.name,
        }
    )
    clear_request_context()


@task_failure.connect
def task_failure_handler(task_id, exception, *args, **kwargs):
    """Log task failures."""
    logger.error(
        "Celery task failed",
        extra={
            "task_id": task_id,
            "exception_type": type(exception).__name__,
            "exception_message": str(exception),
        },
        exc_info=True
    )
    clear_request_context()

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
