import redis.asyncio as redis
import redis as sync_redis

from .config import settings
from contextlib import contextmanager

redis_pool = redis.ConnectionPool.from_url(settings.REDIS_URL, decode_responses=True)
sync_redis_pool = sync_redis.ConnectionPool.from_url(
    settings.REDIS_URL, decode_responses=True
)


@contextmanager
def sync_get_redis_client():
    client = None
    try:
        client = sync_redis.Redis(connection_pool=sync_redis_pool)
        yield client
    finally:
        if client:
            client.close()


async def get_redis_client():
    """
    Dependency function to get an async Redis client from the connection pool.
    """
    async with redis.Redis(connection_pool=redis_pool) as client:
        yield client
