import json
import redis.asyncio as redis
import redis as sync_redis
from typing import Dict, Any, Optional, List

TRENDING_CACHE_TTL_SECONDS = 86400  # Cache trending movies for 24 hours
LLM_REC_CACHE_TTL_SECONDS = 60 * 60 * 24 * 7


def _get_trending_cache_key(page: int) -> str:
    return f"trending:day:page:{page}"


async def get_cached_trending_movies(
    redis_client: redis.Redis, page: int
) -> Optional[Dict[str, Any]]:
    """Retrieves cached trending movie data from Redis."""
    cache_key = _get_trending_cache_key(page)
    cached_data = await redis_client.get(cache_key)
    if cached_data:
        return json.loads(cached_data)
    return None


async def cache_trending_movies(
    redis_client: redis.Redis, page: int, data: Dict[str, Any]
):
    """Stores trending movie data in Redis with a 24-hour TTL."""
    cache_key = _get_trending_cache_key(page)
    await redis_client.set(cache_key, json.dumps(data), ex=TRENDING_CACHE_TTL_SECONDS)


async def get_cached_llm_recommendation(
    redis_client: redis.Redis, cache_key: str
) -> Optional[List[Dict[str, Any]]]:
    """Retrieves a cached, structured LLM recommendation from Redis."""
    cached_data = await redis_client.get(cache_key)
    if cached_data:
        return json.loads(cached_data)
    return None


def cache_llm_recommendation(
    redis_client: sync_redis.Redis, cache_key: str, data: List[Dict[str, Any]]
):
    """Stores a structured LLM recommendation in Redis."""
    redis_client.set(cache_key, json.dumps(data), ex=LLM_REC_CACHE_TTL_SECONDS)
