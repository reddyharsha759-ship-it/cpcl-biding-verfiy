from celery import Celery
from app.core.config import settings

celery_app = Celery(
    "gem_compliance_worker",
    broker=settings.CELERY_BROKER_URL or settings.redis_uri,
    backend=settings.CELERY_RESULT_BACKEND or settings.redis_uri,
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
)
