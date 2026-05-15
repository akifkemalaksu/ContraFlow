from celery import Celery

from src.config import settings

celery_app = Celery(
    "contraflow",
    broker=settings.celery_broker_url,
    backend=settings.celery_result_backend,
    include=[
        "src.infrastructure.tasks.workers.example",
        "src.infrastructure.tasks.workers.hl_sync",
        "src.infrastructure.tasks.workers.copy_trading",
    ],
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    beat_schedule={
        "hl-sync-assets-hourly": {
            "task": "hl.sync_assets",
            "schedule": 3600.0,
        },
    },
)
