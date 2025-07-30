import json
import os
import sys
from datetime import datetime

import requests
from requests.adapters import HTTPAdapter
from sqlalchemy.exc import SQLAlchemyError
from tqdm import tqdm
from urllib3.util.retry import Retry

sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

from app.core.config import settings
from app.core.database import Base, AsyncSessionLocal, async_engine
from app.crud import crud_movie

# --- CONFIGURABLE FILTERS ---
ORIGINAL_LANGUAGE = "en"
ORIGIN_COUNTRY = "US"

# --- API CONSTANTS ---
TMDB_API_URL = "https://api.themoviedb.org/3"
API_MAX_PAGE_LIMIT = 500
DB_BATCH_SIZE = 1000

BACKUP_FILE_PATH = "scripts/movies_backup.json"


def create_resilient_session() -> requests.Session:
    session = requests.Session()
    retry_strategy = Retry(
        total=5,
        backoff_factor=1,
        status_forcelist=[429, 500, 502, 503, 504],
        allowed_methods=["HEAD", "GET", "OPTIONS"],
    )
    adapter = HTTPAdapter(max_retries=retry_strategy)
    session.mount("https://", adapter)
    session.mount("http://", adapter)
    return session


def get_genre_map(session: requests.Session):
    url = f"{TMDB_API_URL}/genre/movie/list"
    params = {"api_key": settings.TMDB_API_KEY}
    response = session.get(url, params=params)
    response.raise_for_status()
    genres = response.json().get("genres", [])
    return {genre["id"]: genre["name"] for genre in genres}


def discover_initial_movie_data(session: requests.Session):
    print(
        f"Discovering movies for language='{ORIGINAL_LANGUAGE}' and country='{ORIGIN_COUNTRY}'..."
    )
    params = {
        "api_key": settings.TMDB_API_KEY,
        "sort_by": "popularity.desc",
        "page": 1,
        "with_original_language": ORIGINAL_LANGUAGE or None,
        "with_origin_country": ORIGIN_COUNTRY or None,
    }
    response = session.get(f"{TMDB_API_URL}/discover/movie", params=params)
    response.raise_for_status()
    data = response.json()
    return data.get("total_pages", 0), data.get("total_results", 0)


def fetch_all_movies_from_api(session: requests.Session) -> list:
    """
    Fetches all movie data from the API and returns a de-duplicated list of dicts.
    """
    total_pages_api, total_results_api = discover_initial_movie_data(session)
    pages_to_fetch = min(total_pages_api, API_MAX_PAGE_LIMIT)

    print(
        f"TMDb reports {total_results_api} results. We will fetch from {pages_to_fetch} pages."
    )
    if pages_to_fetch == 0:
        return []

    genre_map = get_genre_map(session)
    all_movies = []

    # This prevents sending duplicate IDs in a single batch to the database.
    seen_ids = set()

    with tqdm(total=pages_to_fetch, desc="Fetching Pages") as pbar:
        for page in range(1, pages_to_fetch + 1):
            try:
                response = session.get(
                    f"{TMDB_API_URL}/discover/movie",
                    params={
                        "api_key": settings.TMDB_API_KEY,
                        "sort_by": "popularity.desc",
                        "page": page,
                        "with_original_language": ORIGINAL_LANGUAGE,
                        "with_origin_country": ORIGIN_COUNTRY,
                    },
                )
                response.raise_for_status()

                for movie_data in response.json().get("results", []):
                    movie_id = movie_data.get("id")

                    if (
                        not movie_id
                        or not movie_data.get("overview")
                        or movie_id in seen_ids
                    ):
                        continue

                    # Mark this ID as seen for this run
                    seen_ids.add(movie_id)

                    movie = {
                        "id": movie_data.get("id"),
                        "title": movie_data.get("title"),
                        "overview": movie_data.get("overview"),
                        "release_date": movie_data.get("release_date"),
                        "poster_path": movie_data.get("poster_path"),
                        "genres": [
                            {"id": gid, "name": genre_map.get(gid)}
                            for gid in movie_data.get("genre_ids", [])
                            if gid in genre_map
                        ],
                        "backdrop_path": movie_data.get("backdrop_path"),
                    }
                    all_movies.append(movie)
            except requests.RequestException as e:
                print(
                    f"\nFailed to fetch page {page} after multiple retries: {e}. Skipping page."
                )

            pbar.update(1)

    return all_movies


async def store_movies_in_db(movies: list):
    """
    Takes a list of movies and upserts them into the database in batches.
    Includes exception handling for database operations.
    """
    if not movies:
        print("No movies to store in the database.")
        return

    print(f"\nPreparing to upsert {len(movies)} movies into the database...")
    db = AsyncSessionLocal()
    try:
        async with async_engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

        total_movies_processed = 0
        with tqdm(total=len(movies), desc="Upserting to DB") as pbar:
            for i in range(0, len(movies), DB_BATCH_SIZE):
                batch = movies[i : i + DB_BATCH_SIZE]
                try:
                    await crud_movie.bulk_upsert_movies(db, batch)
                    total_movies_processed += len(batch)
                    pbar.update(len(batch))
                except SQLAlchemyError as e:
                    print(
                        f"\nDatabase error occurred during batch {i//DB_BATCH_SIZE + 1}. Rolling back."
                    )
                    print(f"Error: {e}")
                    await db.rollback()  # Rollback the failed transaction
                    raise

        print(f"\nSuccessfully processed and stored {total_movies_processed} movies.")

    finally:
        await db.close()


async def main():
    """Main orchestration function."""

    # --- Stage 1: Fetching data from API ---
    print("--- Stage 1: Fetching data from TMDb API ---")
    session = create_resilient_session()
    try:
        all_movies = fetch_all_movies_from_api(session)
    finally:
        session.close()

    if not all_movies:
        print("No movies fetched from API. Exiting.")
        return

    # --- Stage 2: Backing up data to local file ---
    print(
        f"\n--- Stage 2: Backing up {len(all_movies)} movies to {BACKUP_FILE_PATH} ---"
    )
    try:
        with open(BACKUP_FILE_PATH, "w", encoding="utf-8") as f:
            json.dump(all_movies, f, ensure_ascii=False, indent=4)
        print(f"Successfully created local backup.")
    except IOError as e:
        print(f"Error writing to backup file: {e}")
        # We can still proceed to the database stage even if backup fails.

    # Convert release_date strings to date objects
    for movie in all_movies:
        release_date_str = movie.get("release_date")
        if release_date_str and isinstance(release_date_str, str):
            try:
                movie["release_date"] = datetime.fromisoformat(release_date_str).date()
            except ValueError:
                movie["release_date"] = None
        else:
            movie["release_date"] = None

    # --- Stage 3: Storing data in database ---
    print(f"\n--- Stage 3: Storing movies in PostgreSQL database ---")
    try:
        await store_movies_in_db(all_movies)
    except Exception as e:
        print(
            f"\nAn unrecoverable error occurred during the database storage phase: {e}"
        )
        print("Please check the database connection and logs.")
        print(
            f"The fetched data is safely stored in '{BACKUP_FILE_PATH}' for a future retry."
        )


if __name__ == "__main__":
    import asyncio

    print("--- Starting Metadata Ingestion Process ---")
    asyncio.run(main())
    print("--- Metadata Ingestion Process Finished ---")
