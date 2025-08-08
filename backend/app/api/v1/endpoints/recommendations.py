import hashlib
import redis.asyncio as redis
from fastapi import APIRouter, Depends, status, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from neo4j import Driver

from app import schemas
from workers.celery_config import celery_app
from app.core.database import get_async_db
from app.core.redis import get_redis_client
from app.core.graph import get_graph_driver
from app.crud import crud_movie, crud_cache, crud_recommendation
from app.core.embedding_model import get_embedding_model

router = APIRouter()
model = get_embedding_model()


@router.post(
    "",
    response_model=schemas.recommendation.RecResponse,
    status_code=status.HTTP_200_OK,
)
async def get_advanced_recommendations(
    request: schemas.recommendation.RecRequest,
    db: AsyncSession = Depends(get_async_db),
    redis_client: redis.Redis = Depends(get_redis_client),
    driver: Driver = Depends(get_graph_driver),
):

    source_movie = await crud_movie.get_movie_by_id(db, request.source_movie_id)
    if not source_movie:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Source movie with ID {request.source_movie_id} not found.",
        )

    valid_keywords = {
        kw.replace(".", "").lower() for kw in (source_movie.ai_keywords or [])
    }
    selected_keywords = set()
    if request.selected_keywords:
        selected_keywords = {
            kw.replace(".", "").lower() for kw in request.selected_keywords
        }

        if not selected_keywords.issubset(valid_keywords):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="One or more selected keywords are not valid for this movie.",
            )

        keywords_str = "".join(sorted(request.selected_keywords))
        trigger_hash = hashlib.sha256(
            f"{request.source_movie_id}:{keywords_str}".encode()
        ).hexdigest()
        cache_key = f"llm_rec:{trigger_hash}"
        print(f"{request.source_movie_id}:{keywords_str}")

        # Check Redis cache first (hot cache)
        cached_result = await crud_cache.get_cached_llm_recommendation(
            redis_client, cache_key
        )

        # If Redis cache not found, check database (warm cache)
        if not cached_result:
            cached_result = (
                await crud_recommendation.get_recommendations_by_trigger_hash(
                    db, trigger_hash
                )
            )

        if cached_result:
            return {
                "status": "complete",
                "results": cached_result,
            }

    query = crud_movie.create_query_description(
        source_movie.title,
        source_movie.overview,
        [genre["name"] for genre in (source_movie.genres or [])],
        list(valid_keywords),
        list(selected_keywords) or [],
    )
    print(f"Query: {query}")
    embedding = model.encode(query, convert_to_tensor=True).tolist()
    fallback_results = await crud_movie.vector_search(db, source_movie.id, embedding)

    # cache miss
    # fallback_results = await crud_movie.get_fallback_recommendations(
    #     db, driver, request.source_movie_id
    # )

    if request.selected_keywords:
        celery_app.send_task(
            "tasks.generate_and_cache_llm_rec",
            args=[request.source_movie_id, request.selected_keywords, trigger_hash],
            queue="llm_queue",
        )

    return {
        "status": "partial",
        "results": fallback_results,
    }
