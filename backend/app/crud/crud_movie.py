from typing import Any, Dict, List, Set, Callable
from sqlalchemy import select, or_, and_
from neo4j import Driver
from sqlalchemy import insert, func
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from ..models.movie import Movie
from app.schemas.movie import MovieSearchResult
from app.schemas.recommendation import LLMRecResult
from sqlalchemy.orm import Session
from datetime import datetime
import time


def chunker(seq, size):
    return (seq[pos : pos + size] for pos in range(0, len(seq), size))


async def get_existing_movie_ids(db: AsyncSession) -> Set[int]:
    result = await db.execute(select(Movie.id))
    return {id_tuple[0] for id_tuple in result.all()}


def bulk_create_movies(db: Session, movies: List[Dict[str, Any]]):
    if not movies:
        return

    BATCH_SIZE = 1000

    for i, movie_batch in enumerate(chunker(movies, BATCH_SIZE)):
        print(f"Creating movies: Batch {i+1} with {len(movie_batch)} movies")
        try:
            db.execute(insert(Movie), movie_batch)
            db.commit()
        except Exception as e:
            with open("error_log.txt", "a") as error_file:
                error_file.write(f"Error during bulk create: {e}\n")
            db.rollback()
            print(f"Error during batch {i+1}: {e}")


async def bulk_upsert_movies(db: AsyncSession, movies: List[Dict[str, Any]]):
    """
    Performs a bulk "upsert" (insert or update) of movies into the database.
    If a movie with the same ID already exists, it will be updated.
    If it does not exist, it will be inserted.
    """
    if not movies:
        return

    BATCH_SIZE = 1000  # This will create about 13,000 parameters per batch, well under the 32k limit.

    for i, movie_batch in enumerate(chunker(movies, BATCH_SIZE)):
        print(f"Processing batch {i+1} with {len(movie_batch)} movies...")
        try:
            stmt = insert(Movie.__table__).values(movie_batch)

            update_dict = {c.name: c for c in stmt.excluded if c.name != "id"}

            upsert_stmt = stmt.on_conflict_do_update(
                index_elements=["id"], set_=update_dict
            )

            await db.execute(upsert_stmt)
            await db.commit()
        except Exception as e:
            with open("error_log.txt", "a") as error_file:
                error_file.write(f"Error during bulk upsert: {e}\n")
            await db.rollback()


async def bulk_patch_movies(db: AsyncSession, movies_data: List[Dict[str, Any]]):
    """
    Performs a general-purpose bulk "PATCH" on the movies table.

    For each dictionary in the list, it updates only the fields provided.
    Each dictionary MUST contain the 'id' key for matching. Other columns
    in the table that are not present in the dictionary will be ignored and
    left untouched in the database.

    Args:
        db: The AsyncSession for database interaction.
        movies_data: A list of dictionaries, where each dictionary represents
                     a movie to patch. e.g., [{"id": 1, "ai_keywords": [...]}]
    """
    if not movies_data:
        return

    BATCH_SIZE = 1000

    print(f"Starting bulk patch for {len(movies_data)} records...")
    for i, movie_batch in enumerate(chunker(movies_data, BATCH_SIZE)):
        if not movie_batch:
            continue

        print(f"Processing batch {i+1} with {len(movie_batch)} movies...")
        try:
            stmt = insert(Movie.__table__).values(movie_batch)

            update_dict = {
                c.name: c
                for c in stmt.excluded
                if c.name in movie_batch[0] and c.name != "id"
            }

            if not update_dict:
                print(f"Batch {i+1} had no fields to update other than 'id'. Skipping.")
                continue

            # On conflict (i.e., the movie 'id' exists), update only the specified fields.
            patch_stmt = stmt.on_conflict_do_update(
                index_elements=["id"], set_=update_dict
            )

            await db.execute(patch_stmt)
            await db.commit()
            print(f"Successfully patched batch {i+1}.")

        except Exception as e:
            print(f"Error during bulk patch on batch {i+1}: {e}")

            await db.rollback()
            with open("patch_error_log.txt", "a") as error_file:
                error_file.write(f"Error: {e}\nBatch Data: {movie_batch}\n\n")

    print("Bulk patch process completed.")


async def get_movie_by_id(db: AsyncSession, movie_id: int) -> Movie | None:
    """Fetches a single movie by its ID from PostgreSQL."""
    result = await db.execute(select(Movie).filter(Movie.id == movie_id))
    return result.scalars().first()


def sync_get_movie_by_id(db: Session, movie_id: int) -> Movie | None:
    """Fetches a single movie by its ID from PostgreSQL."""
    result = db.execute(select(Movie).filter(Movie.id == movie_id))
    return result.scalars().first()


async def get_movies_by_ids(db: Session, movie_ids: List[int]) -> List[Movie]:
    """Fetches multiple movies by their IDs from PostgreSQL."""
    if not movie_ids:
        return []
    result = await db.execute(select(Movie).filter(Movie.id.in_(movie_ids)))
    return result.scalars().all()


async def search_movies_by_title(
    db: AsyncSession, query: str, limit: int = 20
) -> List[MovieSearchResult]:
    """
    Searches for movies by title and returns data structured for the
    MovieSearchResult schema.
    Full-text search is used here;
    """
    query_parts = query.strip().split()
    tsquery_str = " & ".join([part + ":*" for part in query_parts])

    match_condition = func.to_tsvector("english", Movie.title).op("@@")(
        func.to_tsquery("english", tsquery_str)
    )

    rank = func.ts_rank(
        func.to_tsvector("english", Movie.title),
        func.to_tsquery("english", tsquery_str),
    ).label("rank")

    stmt = (
        select(Movie, rank)
        .filter(match_condition, Movie.release_date < datetime.now().date())
        .order_by(rank.desc(), Movie.vote_count.desc().nulls_last())
        .limit(limit)
    )
    result = await db.execute(stmt)

    return result.scalars().all()


async def filter_existing_movie_ids(db: AsyncSession, movie_ids: List[int]) -> Set[int]:
    """
    Takes a list of movie IDs and returns a set containing only the IDs
    that are NOT already in the database.
    """
    if not movie_ids:
        return set()

    result = await db.execute(select(Movie.id).filter(Movie.id.in_(movie_ids)))
    existing_ids = result.scalars().all()

    return set(movie_ids) - set(existing_ids)


async def get_all_movie_ids(db_session_factory: Callable[[], AsyncSession]) -> Set[int]:
    """
    Efficiently fetches all existing movie IDs from the database.
    """
    async with db_session_factory() as db:
        result = await db.execute(
            select(Movie.id).filter(
                Movie.ai_keywords.is_(None),
            )
        )
        return {row[0] for row in result.all()}


def enrich_recommendations_with_db_data(
    db: Session, parsed_recs: Dict[str, List[Dict[str, Any]]]
) -> Dict[str, Any]:
    """
    Takes a list of recommendations parsed from an LLM and enriches them
    with structured data from our PostgreSQL database.

    Args:
        db: The SQLAlchemy session.
        parsed_recs: A Dict[List], e.g.,
                    {movies:[{'movie_title': 'The Prestige', 'release_year': 2006, ...}, ...]}

    Returns:
        A list of dictionaries matching the LLMRecommendationResult schema, ready for caching.
    """
    if not parsed_recs and not parsed_recs.get("movies"):
        return []

    search_conditions = []
    for rec in parsed_recs.get("movies", []):
        title = rec.get("movie_title")
        year = rec.get("release_year")

        if title and isinstance(title, str) and year and isinstance(year, int):
            condition = and_(Movie.title.ilike(title), Movie.release_year == year)
            search_conditions.append(condition)

    if not search_conditions:
        return []

    query = select(Movie).where(or_(*search_conditions))
    result = db.execute(query)
    db_movies = result.scalars().all()

    db_movie_map = {
        (movie.title.lower(), movie.release_year): movie for movie in db_movies
    }

    final_results = []
    for rec in parsed_recs.get("movies", []):
        title = rec.get("movie_title")
        year = rec.get("release_year")

        if not (title and year):
            continue

        matched_movie = db_movie_map.get((title.lower(), year))

        if matched_movie:
            final_object = LLMRecResult(
                id=matched_movie.id,
                title=matched_movie.title,
                overview=matched_movie.overview,
                release_year=matched_movie.release_year,
                poster_path=matched_movie.poster_path,
                justification=rec.get("justification_keywords", []),
                ai_score=rec.get("similarity_score", 0.0),
            )
            final_results.append(final_object.model_dump())
        else:
            with open("request_movie.txt", "a") as file:
                file.write(
                    f"Could not find movie in DB: {title} ({year}). "
                    f"Original data: {rec}\n"
                )

    return final_results


async def get_fallback_recommendations(
    db: AsyncSession, driver: Driver, source_movie_id: int
) -> List[Dict[str, Any]]:

    query = """
    MATCH (source:Movie {tmdb_id: $id})-[r:IS_SIMILAR_TO]->(target:Movie)
    RETURN target.tmdb_id AS tmdb_id, r.effective_score AS effective_score
    ORDER BY r.effective_score DESC
    LIMIT 20
    """
    ranked_recs_from_graph = []
    max_retries = 3
    for attempt in range(max_retries):
        try:
            with driver.session() as session:
                result = session.run(query, id=source_movie_id)
                ranked_recs_from_graph = [
                    {
                        "id": record["tmdb_id"],
                        "effective_score": record["effective_score"],
                    }
                    for record in result
                ]
            break
        except Exception as e:
            print(f"Neo4j query failed on attempt {attempt + 1}/{max_retries}: {e}")
            if attempt < max_retries - 1:
                time.sleep(2**attempt)
            else:
                print("Max retries reached. Giving up.")

    if not ranked_recs_from_graph:
        return []

    similar_ids = [rec["id"] for rec in ranked_recs_from_graph]

    query = select(
        Movie.id, Movie.title, Movie.release_year, Movie.poster_path, Movie.overview
    ).where(Movie.id.in_(similar_ids))
    result = await db.execute(query)

    movies_data_map = {row.id: row for row in result.all()}

    final_results = []
    for rec in ranked_recs_from_graph:
        movie_data = movies_data_map.get(rec["id"])
        if movie_data and movie_data.id and movie_data.title and movie_data.poster_path:
            final_results.append(
                {
                    "id": movie_data.id,
                    "title": movie_data.title,
                    "overview": movie_data.overview,
                    "release_year": movie_data.release_year,
                    "poster_path": movie_data.poster_path,
                }
            )
    return final_results
