# backend/app/crud/crud_movie.py

from sqlalchemy.orm import Session
from typing import List, Dict, Any, Set

from app.models.movie import Movie
from app.schemas.movie import MovieCreate


def get_existing_movie_ids(db: Session) -> Set[int]:
    """
    Retrieves a set of all movie IDs that already exist in the database.
    """
    existing_ids = db.query(Movie.id).all()
    return {id_tuple[0] for id_tuple in existing_ids}


def bulk_create_movies(db: Session, movies: List[Dict[str, Any]]):
    """
    Performs a bulk insert of new movies into the database.
    """
    db.bulk_insert_mappings(Movie, movies)
    db.commit()
