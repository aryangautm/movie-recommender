import os
import sys
import json
import asyncio
import httpx
from tqdm import tqdm
from typing import List, Dict, Any, Set

sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

from app.core.config import settings
from app.core.database import AsyncSessionLocal
from app.crud import crud_movie

# --- CONFIGURATION ---
TMDB_API_URL = "https://api.themoviedb.org/3"
# Fetch more pages to get a wider variety of movies
API_MAX_PAGE_LIMIT = 500
# Limit concurrent requests to TMDb to avoid getting rate-limited
MAX_CONCURRENT_REQUESTS = 10
# Filter out movies with very few votes to improve data quality
MINIMUM_VOTE_COUNT = 50
# Path for local data backup
BACKUP_FILE_PATH = "scripts/movies_backup.json"


async def discover_movie_ids(client: httpx.AsyncClient) -> Set[int]:
    """
    Stage 1: Quickly discover a large set of movie IDs from the /discover endpoint.
    """
    print(f"Discovering up to {API_MAX_PAGE_LIMIT} pages of movie IDs...")
    discovered_ids = set()

    tasks = []
    for page in range(1, API_MAX_PAGE_LIMIT + 1):
        params = {
            "api_key": settings.TMDB_API_KEY,
            "sort_by": "popularity.desc",
            "page": page,
            "include_adult": False,
            "vote_count.gte": MINIMUM_VOTE_COUNT,  # Only get movies with a decent number of votes
        }
        tasks.append(client.get(f"{TMDB_API_URL}/discover/movie", params=params))

    for response in tqdm(
        asyncio.as_completed(tasks), total=len(tasks), desc="Discovering IDs"
    ):
        try:
            res = await response
            res.raise_for_status()
            for movie in res.json().get("results", []):
                if movie.get("id"):
                    discovered_ids.add(movie["id"])
        except httpx.HTTPStatusError as e:
            print(f"Discovery API Error: {e.response.status_code} on page. Skipping.")
        except Exception as e:
            ...
            # print(f"An error occurred during discovery: {e}. Skipping.")

    print(f"Discovered {len(discovered_ids)} unique movie IDs.")
    return discovered_ids


async def fetch_full_movie_details(
    client: httpx.AsyncClient, movie_ids: Set[int]
) -> List[Dict[str, Any]]:
    """
    Stage 2: Fetch full, enriched details for each movie ID using `append_to_response`.
    """
    print(f"Fetching full details for {len(movie_ids)} movies...")
    # A semaphore limits the number of concurrent requests.
    semaphore = asyncio.Semaphore(MAX_CONCURRENT_REQUESTS)
    tasks = []

    for movie_id in movie_ids:

        async def fetch_one(mid):
            async with semaphore:
                try:
                    params = {
                        "api_key": settings.TMDB_API_KEY,
                        "append_to_response": "credits,keywords",
                    }
                    response = await client.get(
                        f"{TMDB_API_URL}/movie/{mid}", params=params
                    )
                    response.raise_for_status()
                    return response.json()
                except httpx.HTTPStatusError:
                    # It's okay if a single movie fails, we just skip it.
                    return None

        tasks.append(fetch_one(movie_id))

    movie_details_list = []
    for response_task in tqdm(
        asyncio.as_completed(tasks), total=len(tasks), desc="Fetching Details"
    ):
        try:
            details = await response_task
            if details:
                movie_details_list.append(details)
        except Exception as e:
            continue
            # print(f"An error occurred while fetching movie details: {e}")

    return movie_details_list


def process_and_format_movies(
    movies_details: List[Dict[str, Any]],
) -> List[Dict[str, Any]]:
    """
    Transforms the raw, rich data from TMDb into the flat structure needed for our database.
    """
    print("Processing and formatting movie data for database ingestion...")
    processed_movies = []
    for data in movies_details:
        # Extract director and cast from the 'credits' part of the response
        director = next(
            (
                {"id": p["id"], "name": p["name"]}
                for p in data.get("credits", {}).get("crew", [])
                if p["job"] == "Director"
            ),
            None,
        )
        top_cast = [
            {"id": p["id"], "name": p["name"]}
            for p in data.get("credits", {}).get("cast", [])[:5]
        ]

        processed_movies.append(
            {
                "id": data["id"],
                "title": data.get("title"),
                "overview": data.get("overview"),
                "release_date": data.get("release_date"),
                "poster_path": data.get("poster_path"),
                "backdrop_path": data.get("backdrop_path"),
                "genres": data.get("genres", []),
                "keywords": data.get("keywords", {}).get("keywords", []),
                "director": director,
                "cast": top_cast,
                "collection": data.get("belongs_to_collection"),
                "vote_count": data.get("vote_count"),
                "vote_average": data.get("vote_average"),
            }
        )
    return processed_movies


async def main():
    """Main orchestration function for the entire ingestion process."""

    # --- Stage 1: Discover Movie IDs ---
    async with httpx.AsyncClient(timeout=20.0) as client:
        # existing_db_ids = await crud_movie.get_all_movie_ids(AsyncSessionLocal)
        # print(f"Found {len(existing_db_ids)} movies already in the database.")

        # discovered_ids = await discover_movie_ids(client)
        # new_ids_to_fetch = discovered_ids - existing_db_ids

        new_ids_to_fetch = await crud_movie.get_all_movie_ids(AsyncSessionLocal)

        if not new_ids_to_fetch:
            print("No new movies to ingest. Exiting.")
            return

    # --- Stage 2: Fetch Full Details for New Movies ---
    async with httpx.AsyncClient(timeout=20.0) as client:
        full_details = await fetch_full_movie_details(client, new_ids_to_fetch)

    if not full_details:
        print("Failed to fetch details for any new movies. Exiting.")
        return

    # --- Stage 3: Process and Backup ---
    movies_to_store = process_and_format_movies(full_details)
    print(f"Processed {len(movies_to_store)} movies ready for storage.")

    print(f"Backing up data to {BACKUP_FILE_PATH}...")
    try:
        with open(BACKUP_FILE_PATH, "w", encoding="utf-8") as f:
            json.dump(movies_to_store, f, ensure_ascii=False, indent=2)
        print("Backup successful.")
    except IOError as e:
        print(f"Warning: Could not write backup file: {e}")

    from datetime import datetime

    for movie in movies_to_store:
        release_date_str = movie.get("release_date")
        if release_date_str and isinstance(release_date_str, str):
            try:
                movie["release_date"] = datetime.fromisoformat(release_date_str).date()
            except ValueError:
                movie["release_date"] = None
        else:
            movie["release_date"] = None

    # --- Stage 4: Store in Database ---
    print("Storing new movies in the database...")
    async with AsyncSessionLocal() as db:
        await crud_movie.bulk_patch_movies(db, movies_to_store)

    print(f"Successfully ingested {len(movies_to_store)} new movies into the database.")


if __name__ == "__main__":
    print("--- Starting Full Metadata Ingestion Process ---")
    asyncio.run(main())
    print("--- Metadata Ingestion Process Finished ---")
