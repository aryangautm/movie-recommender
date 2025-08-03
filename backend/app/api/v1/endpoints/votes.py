import redis.asyncio as redis
from app.celery_worker import celery_app
from app.core.redis import get_redis_client
from app.crud import crud_vote
import app.schemas as schemas
from fastapi import APIRouter, Depends, HTTPException, status

router = APIRouter()


@router.post(
    "/",
    response_model=schemas.vote.VoteResponse,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Create or vote on a user-defined movie link",
)
async def create_or_vote_on_link(
    vote: schemas.vote.VoteCreate,
    redis_client: redis.Redis = Depends(get_redis_client),
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

    celery_app.send_task(
        "tasks.process_similarity_vote", args=[vote.movie_id_1, vote.movie_id_2]
    )

    await crud_vote.record_user_vote(
        redis_client, vote.fingerprint, vote.movie_id_1, vote.movie_id_2
    )

    return {"message": "Your vote has been accepted and is being processed."}
