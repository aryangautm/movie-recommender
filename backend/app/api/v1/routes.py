from fastapi import APIRouter, Depends

from .endpoints import movies, recommendations, request_logs, votes
from app.core.auth import require_api_key

api_router = APIRouter()

api_router.include_router(movies.router, prefix="/movies", tags=["Movies & Search"])
api_router.include_router(votes.router, prefix="/upvote", tags=["Votes"])
api_router.include_router(
    recommendations.router, prefix="/recommendations", tags=["Recommendations"]
)
api_router.include_router(
    request_logs.router,
    prefix="/logs",
    tags=["Request Logs & Monitoring"],
    dependencies=[Depends(require_api_key)],
)
