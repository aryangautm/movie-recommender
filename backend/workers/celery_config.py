from celery import Celery
from app.core.config import settings

celery_app = Celery(
    "movie-recommender", broker=settings.REDIS_URL, backend=settings.REDIS_URL
)
celery_app.config_from_object(settings, namespace="CELERY")

celery_app.conf.task_routes = {
    "workers.ingestion_tasks.*": {"queue": "ingestion_queue"},
    "workers.llm_tasks.*": {"queue": "llm_queue"},
}

celery_app.autodiscover_tasks(["workers.ingestion_tasks", "workers.llm_tasks"])
