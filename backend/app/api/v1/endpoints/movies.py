from typing import List

from fastapi import APIRouter, Depends, HTTPException, Query
from neo4j import Driver
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.graph import get_graph_driver
from app.crud.crud_movie import (
    get_movie_by_id,
    get_movies_by_ids,
    get_similar_movies_from_graph,
    search_movies_by_title,
)
from app.schemas.movie import Movie, MovieSearchResult, SimilarMovie

router = APIRouter()


@router.get("/search", response_model=List[MovieSearchResult])
def search_movies(
    q: str = Query(..., min_length=3, description="Search query for movie titles"),
    db: Session = Depends(get_db),
):
    """
    Search for movies by title.
    """
    movies = search_movies_by_title(db, query=q)
    return movies


@router.get("/movies/{movie_id}", response_model=Movie)
def read_movie(movie_id: int, db: Session = Depends(get_db)):
    """
    Get a single movie by its TMDb ID.
    """
    db_movie = get_movie_by_id(db, movie_id=movie_id)
    if db_movie is None:
        raise HTTPException(status_code=404, detail="Movie not found")
    return db_movie


@router.get("/movies/{movie_id}/similar", response_model=List[SimilarMovie])
def read_similar_movies(
    movie_id: int,
    db: Session = Depends(get_db),
    driver: Driver = Depends(get_graph_driver),
):
    """
    Get a list of similar movies based on AI-powered graph relationships.
    """
    source_movie = get_movie_by_id(db, movie_id=movie_id)
    if not source_movie:
        raise HTTPException(status_code=404, detail="Source movie not found")

    similar_movies_data = get_similar_movies_from_graph(driver, movie_id=movie_id)
    if not similar_movies_data:
        return []

    similar_movie_ids = [movie["tmdb_id"] for movie in similar_movies_data]

    similar_movie_objects = get_movies_by_ids(db, movie_ids=similar_movie_ids)

    movie_map = {movie.id: movie for movie in similar_movie_objects}

    response = []
    for data in similar_movies_data:
        movie_obj = movie_map.get(data["tmdb_id"])
        if movie_obj:
            similar_movie = SimilarMovie(
                **movie_obj.__dict__,
                ai_score=data["ai_score"],
                user_votes=data["user_votes"]
            )
            response.append(similar_movie)

    return response
