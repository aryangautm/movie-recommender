import logging
from celery import Celery
from celery.signals import worker_shutdown
from neo4j import Driver, GraphDatabase
from typing import List, Dict, Any
from app.core.database import SessionLocal
from datetime import datetime
from app.core.config import settings
from app.crud import crud_vote, crud_movie, crud_cache, crud_recommendation
from app.core.tmdb_client import tmdb_client
from app.services import llm_client
from app.core.redis import sync_get_redis_client
from app.utils import llm_parser

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

from .celery_config import celery_app


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


@worker_shutdown.connect
def shutdown_neo4j_driver(**kwargs):
    global neo4j_driver
    if neo4j_driver:
        neo4j_driver.close()
        logger.info("Neo4j driver for Celery worker shut down.")


@celery_app.task(
    name="tasks.process_similarity_vote",
    bind=True,
    autoretry_for=(Exception,),
    retry_kwargs={"max_retries": 3, "countdown": 5},
)
def process_similarity_vote(self, movie_id_1: int, movie_id_2: int):
    """
    The single source of truth for processing a similarity vote.
    It recalculates and updates the effective_score on the graph edge.
    """
    logger.info(f"Processing similarity vote between {movie_id_1} and {movie_id_2}")
    try:
        global DRIVER
        if not DRIVER or not DRIVER.is_open():
            DRIVER = get_neo4j_driver()

        try:
            with SessionLocal() as db:
                if rec_id := crud_recommendation.is_recommendation(
                    db, movie_id_1, movie_id_2
                ):
                    crud_recommendation.increment_recommendation_vote(db, rec_id)
        except Exception as e:
            logger.error(
                f"Failed to increment recommendation vote for {movie_id_1}, {movie_id_2}: {e}"
            )
            pass

        success = crud_vote.process_similarity_vote_in_graph(
            DRIVER, movie_id_1, movie_id_2
        )

        if success:
            logger.info("Successfully processed vote and updated effective_score.")
        else:
            logger.warning("Vote processing failed for an unknown reason.")

    except Exception as e:
        logger.error(
            f"Task failed for vote between ({movie_id_1}, {movie_id_2}). Error: {e}"
        )
        raise self.retry(exc=e)


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

    print(
        f"Parsed {len(parsed_recs.get("movies", []))} recommendations from LLM output."
    )

    with SessionLocal() as db:
        enriched_recs = crud_movie.enrich_recommendations_with_db_data(db, parsed_recs)
        print(
            f"Enriched recommendations with database data: {len(enriched_recs)} found."
        )
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

        final_recs_with_ids = crud_recommendation.bulk_create_llm_recommendations(
            db, recs_to_save
        )

        final_cached_data = []
        rec_map = {rec["recommended_movie_id"]: rec for rec in final_recs_with_ids}
        for enriched_rec in enriched_recs:
            db_rec = rec_map.get(enriched_rec["id"])
            if db_rec:
                final_cached_data.append({**enriched_rec, "id": db_rec["id"]})

    with sync_get_redis_client() as redis_client:
        crud_cache.cache_llm_recommendation(
            redis_client, f"llm_rec:{trigger_hash}", final_cached_data
        )
