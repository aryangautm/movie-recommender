from app.core.config import settings
from celery import Celery

celery_app = Celery(
    "movie-recommender", broker=settings.REDIS_URL, backend=settings.REDIS_URL
)
celery_app.config_from_object(settings, namespace="CELERY")

# You can add more queues and routing rules as needed
celery_app.conf.task_routes = {
    "workers.ingestion_tasks.*": {"queue": "ingestion_queue"},
    # "workers.llm_tasks.*": {"queue": "llm_queue"},
}

celery_app.autodiscover_tasks(["workers.ingestion_tasks"])
