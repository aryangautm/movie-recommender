from fastapi import APIRouter

from .endpoints import movies, votes

api_router = APIRouter()

api_router.include_router(movies.router, prefix="/movies", tags=["Movies & Search"])
api_router.include_router(votes.router, prefix="/votes", tags=["Votes"])
