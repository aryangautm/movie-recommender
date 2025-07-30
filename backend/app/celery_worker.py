import logging
import asyncio
from celery import Celery
from celery.signals import worker_shutdown
from neo4j import Driver, GraphDatabase
from typing import List, Dict, Any
from .core.database import AsyncSessionLocal, async_engine, Base
from .crud import crud_movie as movie_crud
from datetime import datetime
from .core.config import settings
from .crud import crud_movie
from app.core.tmdb_client import tmdb_client

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


@celery_app.task(
    name="tasks.ingest_new_movies",
    autoretry_for=(Exception,),
    retry_kwargs={"max_retries": 2, "countdown": 60},
)
def ingest_new_movies(movies_data: List[Dict[str, Any]]):
    """
    Celery task to ingest a list of new movies into the PostgreSQL database.
    This is a synchronous task that safely runs an async block for DB operations.
    """
    if not movies_data:
        logger.info("ingest_new_movies task received with no data. Exiting.")
        return

    logger.info(f"Received task to ingest {len(movies_data)} new movies.")

    # The synchronous part of the task prepares the data.
    genre_map = tmdb_client.get_genre_map()
    if not genre_map:
        logger.error("Could not fetch genre map. Aborting ingestion task.")
        raise Exception("Failed to get genre map for movie ingestion.")

    movies_to_create = []
    for movie_data in movies_data:
        genres = [
            {"id": gid, "name": genre_map.get(gid, "Unknown")}
            for gid in movie_data.get("genre_ids", [])
        ]
        release_date_str = movie_data.get("release_date")
        movies_to_create.append(
            {
                "id": movie_data.get("id"),
                "title": movie_data.get("title"),
                "overview": movie_data.get("overview"),
                "release_date": datetime.fromisoformat(release_date_str).date(),
                "poster_path": movie_data.get("poster_path"),
                "backdrop_path": movie_data.get("backdrop_path"),
                "genres": genres,
            }
        )

    # This function defines the async database work.
    async def run_database_operations():
        logger.info(f"Connecting to async DB to ingest {len(movies_to_create)} movies.")
        async with AsyncSessionLocal() as db:
            try:
                await crud_movie.bulk_upsert_movies(db, movies_to_create)
                logger.info("Async database ingestion successful.")
            except Exception as e:
                # The context manager handles rollback automatically.
                logger.error(f"Async database ingestion failed: {e}")
                raise

    # asyncio.run() executes the async block and waits for it to complete.
    try:
        asyncio.run(run_database_operations())
    except Exception as e:
        # Re-raise the exception to trigger Celery's retry mechanism.
        raise e
