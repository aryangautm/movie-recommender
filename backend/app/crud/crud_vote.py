from typing import Tuple

import redis.asyncio as redis
from neo4j import Driver

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
    MATCH (a:Movie {tmdb_id: $id1}), (b:Movie {tmdb_id: $id2})
    MERGE (a)-[r:IS_SIMILAR_TO]-(b)
    ON CREATE SET r.user_votes = 1, r.similarity_score = null, r.ai_score = null
    ON MATCH SET r.user_votes = coalesce(r.user_votes, 0) + 1
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
