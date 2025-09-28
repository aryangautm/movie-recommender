import logging
from typing import List

from app.core.database import SessionLocal
from app.core.redis import sync_get_redis_client
from app.crud import crud_cache, crud_movie, crud_recommendation
from app.services import llm_client
from app.utils import llm_parser

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

from workers.celery_config import celery_app


@celery_app.task(
    name="tasks.generate_and_cache_llm_rec",
    autoretry_for=(Exception,),
    retry_kwargs={"max_retries": 2, "countdown": 120},
)
def generate_and_cache_llm_rec(
    source_movie_id: int, keywords: List[str], trigger_hash: str
):
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

        _ = crud_recommendation.bulk_create_llm_recommendations(db, recs_to_save)

    with sync_get_redis_client() as redis_client:
        crud_cache.cache_llm_recommendation(
            redis_client, f"llm_rec:{trigger_hash}", enriched_recs
        )
