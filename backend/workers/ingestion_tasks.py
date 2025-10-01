import logging
from datetime import datetime
from typing import Any, Dict, List

from app.core.config import settings
from app.core.database import SessionLocal
from app.core.redis import sync_get_redis_client
from app.core.tmdb_client import tmdb_client
from app.crud import crud_movie, crud_processing_queue, crud_recommendation, crud_vote
from app.models.movie import MovieVisibility
from app.models.processing_queue import ProcessingStatus, TriggerSource
from app.models.vote_log import VoteType
from celery.signals import worker_shutdown
from neo4j import Driver, GraphDatabase
from tqdm import tqdm
from workers.celery_config import celery_app

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

neo4j_driver: Driver = None


def get_neo4j_driver():
    global neo4j_driver
    if neo4j_driver is None or neo4j_driver._closed:
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


DRIVER = get_neo4j_driver()


@worker_shutdown.connect
def shutdown_neo4j_driver(**kwargs):  # It needs to accept kwargs
    global neo4j_driver
    if neo4j_driver:
        neo4j_driver.close()
        logger.info("Neo4j driver for Celery worker shut down.")


# Picks pending tasks from the processing queue table
@celery_app.task(
    name="tasks.ingest_recommended_movies",
    autoretry_for=(Exception,),
    retry_kwargs={"max_retries": 2, "countdown": 60},
)
def ingest_recommended_movies():
    movies_to_create: List[Dict[str, Any]] = []
    processes_to_update: List[Dict[str, Any]] = []

    with SessionLocal() as db:
        try:
            pending_movies = crud_processing_queue.get_movies_by_sources(
                db,
                [
                    TriggerSource.RECOMMENDATION,
                    TriggerSource.TRENDING,
                    TriggerSource.MANUAL,
                ],
            )
            crud_processing_queue.bulk_patch_process(
                db,
                [
                    {"id": movie.id, "status": ProcessingStatus.PROCESSING}
                    for movie in pending_movies
                ],
            )

            if not pending_movies:
                logger.warning(
                    "No pending movies found in the processing queue. Exiting."
                )
                return

            genre_map = tmdb_client.get_genre_map()
            for movie in tqdm(pending_movies, desc="Processing movies"):
                if movie.release_year and movie.release_year > datetime.now().year:
                    processes_to_update.append(
                        {
                            "id": movie.id,
                            "status": ProcessingStatus.FAILED,
                            "failure_reason": "FUTURE_RELEASE",
                        }
                    )
                    continue

                if movie.source_movie_id:
                    movie_data = tmdb_client.get_movie_by_id(movie.source_movie_id)
                else:
                    movie_data = tmdb_client.search_movie(
                        query=movie.title, release_year=movie.release_year
                    )

                if not movie_data:
                    processes_to_update.append(
                        {
                            "id": movie.id,
                            "status": ProcessingStatus.FAILED,
                            "failure_reason": (
                                "NOT_FOUND"
                                if not movie.source_movie_id
                                else "API_ERROR"
                            ),
                        }
                    )
                    continue

                genres = [
                    {"id": gid, "name": genre_map.get(str(gid), "Unknown")}
                    for gid in movie_data.get("genre_ids", [])
                ]

                release_date_str = movie_data.get("release_date", "")
                if not release_date_str:
                    processes_to_update.append(
                        {
                            "id": movie.id,
                            "status": ProcessingStatus.FAILED,
                            "failure_reason": "NO_RELEASE_DATE",
                        }
                    )
                    continue

                release_date = datetime.fromisoformat(release_date_str).date()
                release_year = release_date.year
                if release_date < datetime.now().date():
                    movie_data = {
                        "id": movie_data.get("id"),
                        "title": movie_data.get("title"),
                        "overview": movie_data.get("overview"),
                        "release_date": release_date,
                        "release_year": release_year,
                        "poster_path": movie_data.get("poster_path"),
                        "backdrop_path": movie_data.get("backdrop_path"),
                        "genres": genres,
                        "additional_keywords": [
                            kw.capitalize()
                            for kw in (movie.properties or {}).get(
                                "justification_keywords", []
                            )
                        ],
                        "vote_count": movie_data.get("vote_count"),
                        "vote_average": movie_data.get("vote_average"),
                        "visibility": MovieVisibility.PUBLIC,
                        "keywords": movie_data.get("keywords", None),
                        "director": movie_data.get("director", None),
                        "cast": movie_data.get("cast", None),
                        "collection": movie_data.get("collection", None),
                        "original_language": movie_data.get("original_language", None),
                        "origin_country": movie_data.get("origin_country", None),
                        "original_title": movie_data.get("original_title", None),
                        "runtime": movie_data.get("runtime", None),
                        "tagline": movie_data.get("tagline", None),
                    }
                    movies_to_create.append(movie_data)

                    processes_to_update.append(
                        {
                            "id": movie.id,
                            "source_movie_id": movie_data.get("id"),
                            "title": movie_data.get("title"),
                            "release_year": release_year,
                            "status": ProcessingStatus.COMPLETED,
                        }
                    )
                else:
                    processes_to_update.append(
                        {
                            "id": movie.id,
                            "status": ProcessingStatus.FAILED,
                            "failure_reason": "FUTURE_RELEASE",
                        }
                    )

            if movies_to_create:
                crud_movie.bulk_upsert_movies(db, movies_to_create)
                logger.info(f"Successfully ingested {len(movies_to_create)} movies.")
            else:
                logger.info("No movies to ingest.")

            if processes_to_update:
                crud_processing_queue.bulk_patch_process(db, processes_to_update)

            db.commit()
            logger.info("Database ingestion successful.")
        except Exception as e:
            db.rollback()
            logger.error(f"Database ingestion failed: {e}")
            raise


@celery_app.task(
    name="tasks.process_similarity_vote",
    autoretry_for=(Exception,),
    retry_kwargs={"max_retries": 3, "countdown": 5},
    bind=True,
)
def process_similarity_vote(self, fingerprint: str, movie_id_1: int, movie_id_2: int):
    """
    The single source of truth for processing a similarity vote.
    It recalculates and updates the effective_score on the graph edge.
    """
    logger.info(f"Processing similarity vote between {movie_id_1} and {movie_id_2}")
    try:
        with SessionLocal() as db:
            if rec_ids := crud_recommendation.get_recommendations(
                db, movie_id_1, movie_id_2
            ):
                for rec_id in rec_ids:
                    crud_recommendation.increment_recommendation_vote(db, rec_id)

                crud_vote.log_vote(
                    db,
                    fingerprint=fingerprint,
                    source_movie_id=movie_id_1,
                    target_movie_id=movie_id_2,
                    vote_type=VoteType.DIRECT_LINK,
                )

                with sync_get_redis_client() as redis_client:
                    crud_vote.record_user_vote(
                        redis_client, fingerprint, movie_id_1, movie_id_2
                    )
            else:
                logger.info(
                    f"No direct recommendation link found between {movie_id_1} and {movie_id_2}."
                )
                return

        try:
            global DRIVER
            if not DRIVER or DRIVER._closed:
                DRIVER = get_neo4j_driver()

            success = crud_vote.process_similarity_vote_in_graph(
                DRIVER, movie_id_1, movie_id_2
            )

            (
                logger.info("Successfully processed vote in graph database.")
                if success
                else logger.error("Failed to process vote in graph database.")
            )

        except:
            ...

    except Exception as e:
        logger.error(
            f"Task failed for vote between ({movie_id_1}, {movie_id_2}). Error: {e}"
        )
        raise self.retry(exc=e)
