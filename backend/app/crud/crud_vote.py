from typing import Tuple

import redis.asyncio as redis

VOTE_COOLDOWN_SECONDS = 86400


def _get_canonical_pair(movie_id_1: int, movie_id_2: int) -> Tuple[int, int]:
    return tuple(sorted((movie_id_1, movie_id_2)))


def _get_redis_key(fingerprint: str, movie_id_1: int, movie_id_2: int) -> str:
    id1, id2 = _get_canonical_pair(movie_id_1, movie_id_2)
    return f"vote:{fingerprint}:{id1}:{id2}"


async def can_user_vote(
    redis_client: redis.Redis, fingerprint: str, movie_id_1: int, movie_id_2: int
) -> bool:
    key = _get_redis_key(fingerprint, movie_id_1, movie_id_2)
    return await redis_client.get(key) is None


async def record_user_vote(
    redis_client: redis.Redis, fingerprint: str, movie_id_1: int, movie_id_2: int
):
    key = _get_redis_key(fingerprint, movie_id_1, movie_id_2)
    await redis_client.set(key, "voted", ex=VOTE_COOLDOWN_SECONDS)
