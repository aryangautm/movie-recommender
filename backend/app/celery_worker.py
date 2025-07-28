import logging

from celery import Celery
from celery.signals import worker_shutdown
from neo4j import Driver, GraphDatabase

from .core.config import settings
from .crud import crud_movie

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

celery_app = Celery("worker", broker=settings.REDIS_URL, backend=settings.REDIS_URL)

celery_app.conf.imports = ("app.celery_worker",)


neo4j_driver: Driver = None


def get_neo4j_driver():
    global neo4j_driver
    if neo4j_driver is None or not neo4j_driver.is_open():
        try:
            neo4j_driver = GraphDatabase.driver(
                settings.NEO4J_URI,
                auth=(settings.NEO4J_USER, settings.NEO4J_PASSWORD),
                keep_alive=True,
                max_connection_lifetime=3600,
            )
            logger.info("Neo4j driver initialized for Celery worker.")
        except Exception as e:
            logger.error(f"Failed to initialize Neo4j driver for worker: {e}")
            raise
    return neo4j_driver


@celery_app.task(
    name="tasks.update_vote_count",
    bind=True,
    autoretry_for=(Exception,),
    retry_kwargs={"max_retries": 3, "countdown": 5},
)
def update_vote_count(self, movie_id_1: int, movie_id_2: int):
    """
    Celery task to increment the vote count for a movie pair relationship.
    """
    logger.info(f"Received task to update vote between {movie_id_1} and {movie_id_2}")
    try:
        driver = get_neo4j_driver()
        success = crud_movie.increment_user_vote_in_graph(
            driver, movie_id_1, movie_id_2
        )
        if success:
            logger.info(
                f"Successfully updated vote for pair ({movie_id_1}, {movie_id_2})"
            )
        else:
            logger.warning(
                f"Could not find relationship to update for pair ({movie_id_1}, {movie_id_2})"
            )
    except Exception as e:
        logger.error(
            f"Task failed for pair ({movie_id_1}, {movie_id_2}). Retrying... Error: {e}"
        )
        raise self.retry(exc=e)


@worker_shutdown.connect
def shutdown_neo4j_driver(**kwargs):
    global neo4j_driver
    if neo4j_driver:
        neo4j_driver.close()
        logger.info("Neo4j driver for Celery worker shut down.")
