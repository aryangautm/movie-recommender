from typing import Tuple

import redis.asyncio as redis
from neo4j import Driver, exceptions

VOTE_COOLDOWN_SECONDS = 86400
REC_VOTE_COOLDOWN_SECONDS = 90 * 24 * 60 * 60


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


def increment_user_vote_in_graph(
    driver: Driver, movie_id_1: int, movie_id_2: int
) -> bool:
    """
    Finds the relationship between two movies and atomically increments the
    user_votes counter. This is designed to be idempotent.
    Returns True on success, False on failure (e.g., relationship not found).
    """
    # The query will only update the relationship
    # if it already exists between the two specified nodes.
    query = """
    MATCH (a:Movie {tmdb_id: $id1})
    MATCH (b:Movie {tmdb_id: $id2})
    MERGE (a)-[r:IS_SIMILAR_TO]-(b)
    SET r.user_votes = coalesce(r.user_votes, 0) + 1
    RETURN r
    """
    try:
        with driver.session() as session:
            result = session.run(query, id1=movie_id_1, id2=movie_id_2)
            # Check if the update actually found and returned a relationship
            return result.single() is not None
    except exceptions.ServiceUnavailable:
        # Re-raise the exception so Celery's retry mechanism can catch it
        raise
    except Exception as e:
        print(f"An unexpected error occurred while incrementing vote: {e}")
        return False


def _get_rec_vote_redis_key(fingerprint_id: str, recommendation_id: int) -> str:
    """Creates a consistent, namespaced Redis key for a recommendation vote."""
    return f"rec_vote:{fingerprint_id}:{recommendation_id}"


async def can_user_vote_on_recommendation(
    redis_client: redis.Redis, fingerprint_id: str, recommendation_id: int
) -> bool:
    """
    Checks if a user (by fingerprint) has already voted on a specific
    LLM recommendation.
    Returns True if the user is allowed to vote, False otherwise.
    """
    key = _get_rec_vote_redis_key(fingerprint_id, recommendation_id)
    # The user can vote if the key does not exist in Redis.
    return await redis_client.get(key) is None


async def record_recommendation_vote(
    redis_client: redis.Redis, fingerprint_id: str, recommendation_id: int
):
    """
    Records a user's vote on a specific LLM recommendation in Redis to
    prevent duplicate votes. Sets a long-term expiration on the key.
    """
    key = _get_rec_vote_redis_key(fingerprint_id, recommendation_id)
    # The value "1" is arbitrary;
    await redis_client.set(key, "1", ex=REC_VOTE_COOLDOWN_SECONDS)
