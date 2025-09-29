import redis.asyncio as redis
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

import app.schemas as schemas
from app.core.database import get_db
from app.core.redis import get_redis_client
from app.crud import crud_recommendation, crud_vote
from workers.celery_config import celery_app

router = APIRouter()


@router.post(
    "",
    response_model=schemas.vote.VoteResponse,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Create or vote on a user-defined movie link",
)
async def create_or_vote_on_link(
    vote: schemas.vote.VoteCreate,
    redis_client: redis.Redis = Depends(get_redis_client),
    db: Session = Depends(get_db),
):
    if vote.movie_id_1 == vote.movie_id_2:
        raise HTTPException(
            status_code=400, detail="Movies cannot be linked to themselves."
        )

    if not await crud_vote.can_user_vote(
        redis_client, vote.fingerprint, vote.movie_id_1, vote.movie_id_2
    ):
        raise HTTPException(
            status_code=429, detail="You have already voted for this link recently."
        )

    if await crud_vote.is_limit_exceeded(redis_client, vote.fingerprint):
        raise HTTPException(
            status_code=429, detail="You have exceeded your daily voting limit."
        )

    if not crud_recommendation.get_recommendations(
        db, vote.movie_id_1, vote.movie_id_2
    ):
        raise HTTPException(
            status_code=400,
            detail="No recommendation link exists between the two movies.",
        )

    celery_app.send_task(
        "tasks.process_similarity_vote",
        args=[vote.fingerprint, vote.movie_id_1, vote.movie_id_2],
        queue="ingestion_queue",
    )

    return {"message": "Your vote has been accepted and is being processed."}
