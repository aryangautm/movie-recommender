from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from typing import List, Dict, Any, Optional, Tuple

from ..models.recommendation import LlmRecommendation
from app.models.movie import Movie
from sqlalchemy.orm import Session


def bulk_create_llm_recommendations(
    db: Session, recommendations_data: List[Dict[str, Any]]
) -> List[Dict[str, Any]]:
    """
    Inserts a list of new LLM recommendations into the database and returns
    them enriched with their new database IDs.
    """
    if not recommendations_data:
        return []

    new_recs = [LlmRecommendation(**data) for data in recommendations_data]
    db.add_all(new_recs)

    db.flush(new_recs)

    for rec_obj, rec_data in zip(new_recs, recommendations_data):
        rec_data["id"] = rec_obj.id

    db.commit()
    return recommendations_data


def is_recommendation(db: Session, movie_id_1: int, movie_id_2: int) -> bool:
    if movie_id_1 == movie_id_2:
        return None

    stmt = select(LlmRecommendation).where(
        (LlmRecommendation.source_movie_id == movie_id_1)
        & (LlmRecommendation.recommended_movie_id == movie_id_2)
    )
    result = db.execute(stmt)
    return result.scalar_one_or_none()


async def get_recommendation_by_id(
    db: AsyncSession, rec_id: int
) -> Optional[LlmRecommendation]:
    """Fetches a single LLM recommendation by its primary key."""
    result = await db.execute(
        select(LlmRecommendation).where(LlmRecommendation.id == rec_id)
    )
    return result.scalar_one_or_none()


def increment_recommendation_vote(
    db: Session, rec_id: int
) -> Optional[Tuple[int, int]]:
    """
    Atomically increments the vote count for a specific recommendation.
    Returns the (source_movie_id, recommended_movie_id) pair on success.
    """
    stmt = (
        update(LlmRecommendation)
        .where(LlmRecommendation.id == rec_id)
        .values(user_votes=LlmRecommendation.user_votes + 1)
        .returning(
            LlmRecommendation.source_movie_id, LlmRecommendation.recommended_movie_id
        )
    )
    result = db.execute(stmt)
    db.commit()

    updated_row = result.first()
    return updated_row if updated_row else None


async def get_recommendations_by_trigger_hash(
    db: AsyncSession, trigger_hash: str
) -> List[Dict[str, Any]]:
    """
    Fetches all recommendations for a given trigger hash and enriches them
    with movie details for the frontend.
    """
    stmt = (
        select(
            LlmRecommendation.id.label("recommendation_id"),
            LlmRecommendation.llm_justification,
            LlmRecommendation.llm_score,
            Movie.id,
            Movie.title,
            Movie.release_year,
            Movie.poster_path,
        )
        .join(Movie, LlmRecommendation.recommended_movie_id == Movie.id)
        .where(LlmRecommendation.trigger_keywords_hash == trigger_hash)
        .order_by(LlmRecommendation.llm_score.desc())
    )

    result = await db.execute(stmt)
    rows = result.all()

    recommendations = [
        {
            "id": row.id,
            "title": row.title,
            "release_year": row.release_year,
            "poster_path": row.poster_path,
            "justification": row.llm_justification,
            "score": row.llm_score,
            "recommendation_id": row.recommendation_id,
        }
        for row in rows
    ]
    return recommendations
