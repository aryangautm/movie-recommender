from typing import Any, Dict, List, Set

from neo4j import Driver, exceptions
from sqlalchemy import desc
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import Session

from ..models.movie import Movie


def get_existing_movie_ids(db: Session) -> Set[int]:
    existing_ids = db.query(Movie.id).all()
    return {id_tuple[0] for id_tuple in existing_ids}


def bulk_create_movies(db: Session, movies: List[Dict[str, Any]]):
    db.bulk_insert_mappings(Movie, movies)
    db.commit()


def bulk_upsert_movies(db: Session, movies: List[Dict[str, Any]]):
    """
    Performs a bulk "upsert" (insert or update) of movies into the database.
    If a movie with the same ID already exists, it will be updated.
    If it does not exist, it will be inserted.
    """
    if not movies:
        return

    stmt = insert(Movie.__table__).values(movies)

    # Define what to do on conflict (i.e., when a movie ID already exists)
    # We update all columns except for the 'id' itself.
    update_dict = {c.name: c for c in stmt.excluded if c.name != "id"}

    upsert_stmt = stmt.on_conflict_do_update(index_elements=["id"], set_=update_dict)

    db.execute(upsert_stmt)
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


def increment_user_vote_in_graph(
    driver: Driver, movie_id_1: int, movie_id_2: int
) -> bool:
    """
    Finds the relationship between two movies and atomically increments the
    user_votes counter. This is designed to be idempotent.
    Returns True on success, False on failure (e.g., relationship not found).
    """
    # The query will only update the relationship
    # if it already exists between the two specified nodes.
    query = """
    MATCH (a:Movie {tmdb_id: $id1})
    MATCH (b:Movie {tmdb_id: $id2})
    // We match the relationship in either direction
    MERGE (a)-[r:IS_SIMILAR_TO]-(b)
    SET r.user_votes = coalesce(r.user_votes, 0) + 1
    RETURN r
    """
    try:
        with driver.session() as session:
            result = session.run(query, id1=movie_id_1, id2=movie_id_2)
            # Check if the update actually found and returned a relationship
            return result.single() is not None
    except exceptions.ServiceUnavailable:
        # Re-raise the exception so Celery's retry mechanism can catch it
        raise
    except Exception as e:
        print(f"An unexpected error occurred while incrementing vote: {e}")
        return False
