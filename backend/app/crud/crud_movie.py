from sqlalchemy.orm import Session
from sqlalchemy import desc
from neo4j import Driver
from typing import List, Dict, Any, Set

from ..models.movie import Movie


def get_existing_movie_ids(db: Session) -> Set[int]:
    existing_ids = db.query(Movie.id).all()
    return {id_tuple[0] for id_tuple in existing_ids}


def bulk_create_movies(db: Session, movies: List[Dict[str, Any]]):
    db.bulk_insert_mappings(Movie, movies)
    db.commit()


def get_movie_by_id(db: Session, movie_id: int) -> Movie | None:
    """Fetches a single movie by its ID from PostgreSQL."""
    return db.query(Movie).filter(Movie.id == movie_id).first()


def get_movies_by_ids(db: Session, movie_ids: List[int]) -> List[Movie]:
    """Fetches multiple movies by their IDs from PostgreSQL."""
    if not movie_ids:
        return []
    return db.query(Movie).filter(Movie.id.in_(movie_ids)).all()


def search_movies_by_title(db: Session, query: str, limit: int = 20) -> List[Movie]:
    """Searches for movies by title in PostgreSQL (case-insensitive)."""
    return db.query(Movie).filter(Movie.title.ilike(f"%{query}%")).limit(limit).all()


def get_similar_movies_from_graph(
    driver: Driver, movie_id: int, limit: int = 20
) -> List[Dict[str, Any]]:
    """
    Finds movies similar to the given movie_id from Neo4j.
    Returns a list of dictionaries with tmdb_id, ai_score, and user_votes.
    """
    query = """
    MATCH (source:Movie {tmdb_id: $id})-[r:IS_SIMILAR_TO]->(target:Movie)
    RETURN target.tmdb_id AS tmdb_id, r.ai_score AS ai_score, r.user_votes AS user_votes
    ORDER BY r.ai_score DESC
    LIMIT $limit
    """
    with driver.session() as session:
        result = session.run(query, id=movie_id, limit=limit)
        return [record.data() for record in result]
