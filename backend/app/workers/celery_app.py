from celery import Celery
from celery.schedules import crontab

from app.config import settings

celery_app = Celery(
    "llmops",
    broker=settings.redis_url,
    backend=settings.redis_url,
    include=[
        "app.workers.eval_tasks",
        "app.workers.cost_tasks",
        "app.workers.deployment_tasks",
    ],
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    worker_prefetch_multiplier=1,
)

celery_app.conf.beat_schedule = {
    "progress-canary-every-5-min": {
        "task": "app.workers.deployment_tasks.progress_canary",
        "schedule": 300.0,  # 5 minutes
    },
    "check-budgets-every-15-min": {
        "task": "app.workers.cost_tasks.check_budgets",
        "schedule": 900.0,  # 15 minutes
    },
    "generate-cost-forecast-daily": {
        "task": "app.workers.cost_tasks.generate_cost_forecast",
        "schedule": crontab(hour=2, minute=0),
    },
}
