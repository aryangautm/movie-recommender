import redis.asyncio as redis
from app.celery_worker import celery_app
from app.core.redis import get_redis_client
from app.crud import crud_vote
from app.schemas import vote
from fastapi import APIRouter, Depends, HTTPException, status

router = APIRouter()


@router.post(
    "/", response_model=vote.VoteResponse, status_code=status.HTTP_202_ACCEPTED
)
async def create_vote(
    vote: vote.VoteCreate, redis_client: redis.Redis = Depends(get_redis_client)
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
