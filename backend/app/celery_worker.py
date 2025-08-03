import logging
from celery import Celery
from celery.signals import worker_shutdown
from neo4j import Driver, GraphDatabase
from typing import List, Dict, Any
from .core.database import SessionLocal
from datetime import datetime
from .core.config import settings
from .crud import crud_vote, crud_movie, crud_cache, crud_recommendation
from app.core.tmdb_client import tmdb_client
from app.services import llm_client
from app.core.redis import sync_get_redis_client
from app.utils import llm_parser

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


DRIVER = get_neo4j_driver()


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
        success = crud_vote.increment_user_vote_in_graph(DRIVER, movie_id_1, movie_id_2)
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


# @celery_app.task(
#     name="tasks.ingest_new_movies",
#     autoretry_for=(Exception,),
#     retry_kwargs={"max_retries": 2, "countdown": 60},
# )
# def ingest_new_movies(movies_data: List[Dict[str, Any]]):
#     """
#     Celery task to ingest a list of new movies into the PostgreSQL database.
#     This is a synchronous task that safely runs an async block for DB operations.
#     """
#     if not movies_data:
#         logger.info("ingest_new_movies task received with no data. Exiting.")
#         return

#     logger.info(f"Received task to ingest {len(movies_data)} new movies.")

#     # The synchronous part of the task prepares the data.
#     genre_map = tmdb_client.get_genre_map()
#     if not genre_map:
#         logger.error("Could not fetch genre map. Aborting ingestion task.")
#         raise Exception("Failed to get genre map for movie ingestion.")

#     movies_to_create = []
#     for movie_data in movies_data:
#         genres = [
#             {"id": gid, "name": genre_map.get(gid, "Unknown")}
#             for gid in movie_data.get("genre_ids", [])
#         ]
#         release_date_str = movie_data.get("release_date", "")
#         release_year_int = (
#             int(release_date_str.split("-")[0]) if release_date_str else None
#         )
#         movies_to_create.append(
#             {
#                 "id": movie_data.get("id"),
#                 "title": movie_data.get("title"),
#                 "overview": movie_data.get("overview"),
#                 "release_date": release_date_str,
#                 "release_year": release_year_int,
#                 "poster_path": movie_data.get("poster_path"),
#                 "backdrop_path": movie_data.get("backdrop_path"),
#                 "genres": genres,
#             }
#         )

#     # This function defines the async database work.
#     async def run_database_operations():
#         logger.info(f"Connecting to async DB to ingest {len(movies_to_create)} movies.")
#         async with AsyncSessionLocal() as db:
#             try:
#                 for movie in movies_to_create:
#                     release_date_str = movie.get("release_date")
#                     if release_date_str and isinstance(release_date_str, str):
#                         try:
#                             movie["release_date"] = datetime.fromisoformat(
#                                 release_date_str
#                             ).date()
#                         except ValueError:
#                             movie["release_date"] = None
#                     else:
#                         movie["release_date"] = None
#                 await crud_movie.bulk_patch_movies(db, movies_to_create)
#                 logger.info("Async database ingestion successful.")
#             except Exception as e:
#                 # The context manager handles rollback automatically.
#                 logger.error(f"Async database ingestion failed: {e}")
#                 raise

#     # asyncio.run() executes the async block and waits for it to complete.
#     try:
#         asyncio.run(run_database_operations())
#     except Exception as e:
#         # Re-raise the exception to trigger Celery's retry mechanism.
#         raise e


@celery_app.task(
    name="tasks.generate_and_cache_llm_rec",
    autoretry_for=(Exception,),
    retry_kwargs={"max_retries": 2, "countdown": 120},
)
def generate_and_cache_llm_rec(
    source_movie_id: int, keywords: List[str], trigger_hash: str
):
    print("Generating LLM recommendations...")
    with SessionLocal() as db:
        print(
            f"Generating LLM recommendations for movie ID {source_movie_id} with keywords {keywords}."
        )
        movie = crud_movie.sync_get_movie_by_id(db, source_movie_id)

    llm_raw_output = llm_client.generate_recommendations(movie, keywords)
    parsed_recs = llm_parser.parse_llm_recommendations(llm_raw_output)

    print(f"Parsed {len(parsed_recs)} recommendations from LLM output.")

    with SessionLocal() as db:
        # Enrich with DB data (IDs, posters)
        enriched_recs = crud_movie.enrich_recommendations_with_db_data(db, parsed_recs)

        # Prepare data for Postgres insertion
        recs_to_save = [
            {
                "source_movie_id": source_movie_id,
                "trigger_keywords_hash": trigger_hash,
                "recommended_movie_id": rec["id"],
                "llm_justification": rec["justification"],
                "llm_score": rec["ai_score"],
            }
            for rec in enriched_recs
        ]

        # --- THE CRITICAL UPDATE ---
        # Save to Postgres to get IDs, and get the data back enriched with those IDs
        final_recs_with_ids = crud_recommendation.bulk_create_llm_recommendations(
            db, recs_to_save
        )

        # Now, merge the final data for caching
        final_cached_data = []
        rec_map = {rec["recommended_movie_id"]: rec for rec in final_recs_with_ids}
        for enriched_rec in enriched_recs:
            db_rec = rec_map.get(enriched_rec["id"])
            if db_rec:
                final_cached_data.append({**enriched_rec, "id": db_rec["id"]})

    # Cache the ID-enriched result in Redis
    with sync_get_redis_client() as redis_client:
        crud_cache.cache_llm_recommendation(
            redis_client, f"llm_rec:{trigger_hash}", final_cached_data
        )


@celery_app.task(name="tasks.process_recommendation_vote")
def process_recommendation_vote(recommendation_id: int):
    """
    Handles a user's 'Agree?' vote on an LLM recommendation.
    1. Increments the vote in PostgreSQL.
    2. Dispatches a task to update the core Neo4j graph.
    """

    logger.info(f"Processing vote for recommendation ID: {recommendation_id}")
    with SessionLocal() as db:
        # Atomically increment the vote and get the movie IDs back
        movie_pair = crud_recommendation.increment_recommendation_vote(
            db, recommendation_id
        )

    if movie_pair:
        source_id, target_id = movie_pair
        logger.info(
            f"Vote recorded. Promoting link between movies {source_id} and {target_id}."
        )
        # Dispatch the existing task to strengthen the Neo4j graph
        celery_app.send_task("tasks.update_vote_count", args=[source_id, target_id])
    else:
        logger.warning(
            f"Could not find recommendation with ID {recommendation_id} to process vote."
        )
