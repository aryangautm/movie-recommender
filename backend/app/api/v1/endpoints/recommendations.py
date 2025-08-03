import hashlib
import redis.asyncio as redis
from fastapi import APIRouter, Depends, status, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from neo4j import Driver

from app import schemas
from app.celery_worker import celery_app
from app.core.database import get_async_db
from app.core.redis import get_redis_client
from app.core.graph import get_graph_driver
from app.crud import crud_movie, crud_cache

router = APIRouter()


@router.post(
    "/",
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

    valid_keywords = source_movie.ai_keywords or []
    if not set(request.selected_keywords).issubset(valid_keywords):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="One or more selected keywords are not valid for this movie.",
        )

    keywords_str = "".join(sorted(request.selected_keywords))
    trigger_hash = hashlib.sha256(
        f"{request.source_movie_id}:{keywords_str}".encode()
    ).hexdigest()
    cache_key = f"llm_rec:{trigger_hash}"

    cached_result = await crud_cache.get_cached_llm_recommendation(
        redis_client, cache_key
    )
    if cached_result:
        return {
            "status": "complete",
            "results": cached_result,
        }

    # cache miss
    fallback_results = await crud_movie.get_fallback_recommendations(
        db, driver, request.source_movie_id, request.selected_keywords
    )

    celery_app.send_task(
        "tasks.generate_and_cache_llm_rec",
        args=[request.source_movie_id, request.selected_keywords, trigger_hash],
    )

    return {
        "status": "partial",
        "results": fallback_results,
    }
