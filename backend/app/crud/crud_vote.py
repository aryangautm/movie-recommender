from typing import Tuple

import redis.asyncio as redis
from neo4j import Driver
from app.models.vote_log import VoteLog, VoteType
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.config import settings

VOTE_COOLDOWN_SECONDS = 90 * 24 * 60 * 60


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


def process_similarity_vote_in_graph(
    driver: Driver, movie_id_1: int, movie_id_2: int
) -> bool:
    """
    Handles a vote for a similarity link. It creates the link if it doesn't
    exist, increments the vote, recalculates the effective_score, and updates the edge.
    This is designed to be run inside a Celery task.
    """
    from ..utils.scoring import calculate_effective_score

    query = """
    MATCH (a:Movie {tmdb_id: $id1})
    MATCH (b:Movie {tmdb_id: $id2})
    MERGE (a)-[r:IS_SIMILAR_TO]-(b)
    ON CREATE SET
        r.user_votes = 1,
        r.similarity_score = null,
        r.ai_score = null
    ON MATCH SET
        r.user_votes = coalesce(r.user_votes, 0) + 1
    RETURN
        r.user_votes AS user_votes,
        r.ai_score AS ai_score,
        r.similarity_score AS similarity_score
    """
    with driver.session() as session:
        result = session.run(query, id1=movie_id_1, id2=movie_id_2)
        current_scores = result.single()

        if not current_scores:
            return False

        new_effective_score = calculate_effective_score(
            user_votes=current_scores["user_votes"],
            ai_score=current_scores["ai_score"],
            similarity_score=current_scores["similarity_score"],
        )

        update_query = """
        MATCH (:Movie {tmdb_id: $id1})-[r:IS_SIMILAR_TO]-(:Movie {tmdb_id: $id2})
        SET r.effective_score = $score
        """
        session.run(
            update_query, id1=movie_id_1, id2=movie_id_2, score=new_effective_score
        )
        return True


async def log_vote(
    db: AsyncSession,
    fingerprint_id: str,
    source_movie_id: int,
    target_movie_id: int,
    vote_type: VoteType,
    reference_id: int | None = None,
):
    """Logs a vote to the persistent audit trail in PostgreSQL."""
    log_entry = VoteLog(
        fingerprint_id=fingerprint_id,
        source_movie_id=source_movie_id,
        target_movie_id=target_movie_id,
        vote_type=vote_type,
        reference_id=reference_id,
    )
    db.add(log_entry)
    await db.commit()


def _get_daily_count_key(fingerprint_id: str) -> str:
    """Creates a Redis key for the daily vote counter."""
    return f"vote_count:daily:{fingerprint_id}"


async def check_and_increment_daily_vote_count(
    redis_client: redis.Redis, fingerprint_id: str
) -> bool:
    """
    Atomically increments the daily vote counter for a fingerprint and checks if
    it has exceeded the limit. Returns True if the vote is allowed, False otherwise.
    """
    key = _get_daily_count_key(fingerprint_id)

    # Use a pipeline for an atomic transaction
    pipe = redis_client.pipeline()
    pipe.incr(key)
    pipe.expire(key, 86400, nx=True)  # Set a 24h expiry only if the key is new
    results = await pipe.execute()

    current_count = results[0]

    return current_count <= settings.MAX_VOTES_PER_DAY
