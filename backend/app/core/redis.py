import redis.asyncio as redis

from .config import settings

redis_pool = redis.ConnectionPool.from_url(settings.REDIS_URL, decode_responses=True)


async def get_redis_client():
    """
    Dependency function to get an async Redis client from the connection pool.
    """
    async with redis.Redis(connection_pool=redis_pool) as client:
        yield client
