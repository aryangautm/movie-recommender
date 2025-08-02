from typing import Any, Dict, List, Set, Callable

from neo4j import Driver, exceptions
from sqlalchemy import insert, func
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from ..models.movie import Movie
from app.schemas.movie import MovieSearchResult, Genre


async def get_existing_movie_ids(db: AsyncSession) -> Set[int]:
    result = await db.execute(select(Movie.id))
    return {id_tuple[0] for id_tuple in result.all()}


async def bulk_create_movies(db: AsyncSession, movies: List[Dict[str, Any]]):
    if not movies:
        return
    await db.execute(insert(Movie), movies)
    await db.commit()


def chunker(seq, size):
    return (seq[pos : pos + size] for pos in range(0, len(seq), size))


async def bulk_upsert_movies(db: AsyncSession, movies: List[Dict[str, Any]]):
    """
    Performs a bulk "upsert" (insert or update) of movies into the database.
    If a movie with the same ID already exists, it will be updated.
    If it does not exist, it will be inserted.
    """
    if not movies:
        return

    BATCH_SIZE = 1000  # This will create about 13,000 parameters per batch, well under the 32k limit.

    # Process the movies in batches
    for i, movie_batch in enumerate(chunker(movies, BATCH_SIZE)):
        print(f"Processing batch {i+1} with {len(movie_batch)} movies...")
        try:
            # The core upsert logic is the same, but applied to the BATCH
            stmt = insert(Movie.__table__).values(movie_batch)

            update_dict = {c.name: c for c in stmt.excluded if c.name != "id"}

            upsert_stmt = stmt.on_conflict_do_update(
                index_elements=["id"], set_=update_dict
            )

            await db.execute(upsert_stmt)
            await db.commit()  # Commit after each successful batch
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


async def get_movies_by_ids(db: AsyncSession, movie_ids: List[int]) -> List[Movie]:
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
        .filter(match_condition)
        .order_by(rank.desc(), Movie.vote_count.desc().nulls_last())
        .limit(limit)
    )
    result = await db.execute(stmt)

    return result.scalars().all()


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
        result = await db.execute(select(Movie.id).filter(Movie.vote_count == 0))
        return {row[0] for row in result.all()}
