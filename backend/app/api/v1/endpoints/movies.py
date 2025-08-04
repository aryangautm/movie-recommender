import json
import httpx
import asyncio
from typing import List
import redis.asyncio as redis
from app.core.database import get_async_db
from app.core.redis import get_redis_client
from app.crud.crud_movie import (
    get_movie_by_id,
    search_movies_by_title,
    filter_existing_movie_ids,
)
from app.crud.crud_cache import get_cached_trending_movies, cache_trending_movies
from app.schemas.movie import Movie, MovieSearchResult, SimilarMovie, TrendingMoviesPage
from fastapi import APIRouter, Depends, HTTPException, Query
from neo4j import Driver
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.tmdb_client import tmdb_client
from app.celery_worker import celery_app

router = APIRouter()
CACHE_TTL_SECONDS = 86400


@router.get("/trending", response_model=TrendingMoviesPage)
async def get_trending_movies(
    page: int = Query(1, ge=1, description="Page number to fetch"),
    db: AsyncSession = Depends(get_async_db),
    redis_client: redis.Redis = Depends(get_redis_client),
):
    """
    Get the daily trending movies.
    - Results are cached for 24 hours to reduce API calls.
    - New movies discovered in the trending list are automatically added
      to our database in the background.
    """
    # 1. Check cache first
    cached_data = await get_cached_trending_movies(redis_client, page=page)
    if cached_data:
        return cached_data

    # 2. If cache miss, fetch from TMDb
    genre_map_task = asyncio.to_thread(tmdb_client.get_genre_map)
    trending_data_task = tmdb_client.fetch_trending_from_tmdb(page=page)

    genre_map, trending_data = await asyncio.gather(genre_map_task, trending_data_task)

    trending_data = await tmdb_client.fetch_trending_from_tmdb(page=page)
    if not trending_data:
        raise HTTPException(
            status_code=503,
            detail="Could not fetch trending movies from external service.",
        )
    for movie in trending_data.get("results", []):
        movie["genres"] = [
            {"id": gid, "name": genre_map.get(gid, "Unknown")}
            for gid in movie.get("genre_ids", [])
        ]

    # 3. Cache the new data
    await cache_trending_movies(redis_client, page=page, data=trending_data)

    # 4. Asynchronously sync new movies to our database
    trending_movies = trending_data.get("results", [])
    if trending_movies:
        movie_ids = [movie["id"] for movie in trending_movies]

        # This DB call is synchronous but very fast (a single indexed query)
        new_movie_ids = await filter_existing_movie_ids(db, movie_ids)

        # if new_movie_ids:
        #     new_movies_data = [
        #         movie for movie in trending_movies if movie["id"] in new_movie_ids
        #     ]
        #     # Dispatch the background task and DO NOT wait for it
        #     celery_app.send_task("tasks.ingest_new_movies", args=[new_movies_data])

    return trending_data


@router.get("/search", response_model=List[MovieSearchResult])
async def search_movies(
    q: str = Query(..., min_length=3, description="Search query for movie titles"),
    limit: int = Query(5, ge=1, le=40, description="Number of results to return"),
    db: AsyncSession = Depends(get_async_db),
):
    """
    Search for movies by title.
    """
    db_movies = await search_movies_by_title(db, query=q, limit=limit)
    movies = []
    for movie in db_movies:
        movie_data = movie.__dict__
        movie_data["keywords"] = [
            keyword.replace(".", "").capitalize() for keyword in movie.ai_keywords or []
        ]
        movies.append(movie_data)
    return movies


@router.get("/{movie_id}", response_model=Movie)
async def read_movie(movie_id: int, db: AsyncSession = Depends(get_async_db)):
    """
    Get a single movie by its TMDb ID.
    """
    db_movie = await get_movie_by_id(db, movie_id=movie_id)
    if db_movie is None:
        raise HTTPException(status_code=404, detail="Movie not found")
    return db_movie
