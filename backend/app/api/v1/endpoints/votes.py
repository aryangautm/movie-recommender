import redis.asyncio as redis
from app.celery_worker import celery_app
from app.core.redis import get_redis_client
from app.crud import crud_vote, crud_recommendation
import app.schemas as schemas
from fastapi import APIRouter, Depends, HTTPException, status
from app.core.database import get_async_db
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter()


@router.post(
    "/", response_model=schemas.vote.VoteResponse, status_code=status.HTTP_202_ACCEPTED
)
async def create_vote(
    vote: schemas.vote.VoteCreate, redis_client: redis.Redis = Depends(get_redis_client)
):
    if vote.movie_id_1 == vote.movie_id_2:
        raise HTTPException(
            status_code=400, detail="A movie cannot be similar to itself."
        )

    if not await crud_vote.can_user_vote(
        redis_client, vote.fingerprint, vote.movie_id_1, vote.movie_id_2
    ):
        raise HTTPException(
            status_code=429,
            detail="You have already voted for this movie pair recently.",
        )

    celery_app.send_task(
        "tasks.update_vote_count", args=[vote.movie_id_1, vote.movie_id_2]
    )

    await crud_vote.record_user_vote(
        redis_client, vote.fingerprint, vote.movie_id_1, vote.movie_id_2
    )

    return {"message": "Vote accepted and is being processed."}


@router.post(
    "/{recommendation_id}/upvote",
    response_model=schemas.vote.VoteResponse,
    status_code=status.HTTP_202_ACCEPTED,
)
async def vote_on_recommendation(
    recommendation_id: int,
    fingerprint: schemas.vote.Fingerprint,
    db: AsyncSession = Depends(get_async_db),
    redis_client: redis.Redis = Depends(get_redis_client),
):
    """
    Submits a vote of agreement for a specific LLM-generated recommendation.
    """
    # 1. Idempotency Check: Prevent a user from spamming the same "Agree" button
    if not await crud_vote.can_user_vote_on_recommendation(
        redis_client, fingerprint.id, recommendation_id
    ):
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="You have already voted on this specific recommendation.",
        )

    # 2. Validation: Ensure the recommendation actually exists before queueing a task
    rec = await crud_recommendation.get_recommendation_by_id(db, recommendation_id)
    if not rec:
        raise HTTPException(status_code=404, detail="Recommendation not found.")

    # 3. Dispatch background task for processing
    celery_app.send_task("tasks.process_recommendation_vote", args=[recommendation_id])

    # 4. Record vote for rate-limiting
    await crud_vote.record_recommendation_vote(
        redis_client, fingerprint.id, recommendation_id
    )

    return {"message": "Your vote has been accepted. Thank you for contributing!"}
