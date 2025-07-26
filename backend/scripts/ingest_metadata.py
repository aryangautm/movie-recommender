import requests
import time
from sqlalchemy.orm import Session
from tqdm import tqdm

from app.core.config import settings
from app.core.database import Base, engine, SessionLocal, Movie

TMDB_API_URL = "https://api.themoviedb.org/3"
MOVIES_TO_FETCH = 50000
MAX_PAGE = 500


def get_genre_map():
    """Fetches the genre ID to name mapping from TMDb."""
    url = f"{TMDB_API_URL}/genre/movie/list"
    params = {"api_key": settings.TMDB_API_KEY}
    response = requests.get(url, params=params)
    response.raise_for_status()
    genres = response.json().get("genres", [])
    return {genre["id"]: genre["name"] for genre in genres}


def fetch_popular_movies(db: Session):
    """Fetches popular movies from TMDb and stores them in the database."""
    print("Fetching genre map...")
    genre_map = get_genre_map()

    movies_to_insert = []
    fetched_movie_ids = set(row[0] for row in db.query(Movie.id).all())
    print(
        f"Found {len(fetched_movie_ids)} existing movies in the database. Will skip these."
    )

    # Using tqdm for a visual progress bar
    with tqdm(total=MOVIES_TO_FETCH, desc="Fetching Movies") as pbar:
        for page in range(1, MAX_PAGE + 1):
            if len(movies_to_insert) + len(fetched_movie_ids) >= MOVIES_TO_FETCH:
                break

            url = f"{TMDB_API_URL}/discover/movie"
            params = {
                "api_key": settings.TMDB_API_KEY,
                "sort_by": "popularity.desc",
                "page": page,
                "include_adult": False,
                "include_video": False,
            }

            try:
                response = requests.get(url, params=params)
                response.raise_for_status()
                data = response.json()

                for movie_data in data.get("results", []):
                    movie_id = movie_data.get("id")
                    if not movie_id or movie_id in fetched_movie_ids:
                        continue

                    # Extract year from release_date string, handle missing dates
                    release_date = movie_data.get("release_date")
                    year = int(release_date.split("-")[0]) if release_date else None

                    # Map genre IDs to names
                    genre_names = [
                        {"id": gid, "name": genre_map.get(gid)}
                        for gid in movie_data.get("genre_ids", [])
                        if genre_map.get(gid)
                    ]

                    movie = {
                        "id": movie_id,
                        "title": movie_data.get("title"),
                        "overview": movie_data.get("overview"),
                        "release_year": year,
                        "poster_path": movie_data.get("poster_path"),
                        "genres": genre_names,
                    }
                    movies_to_insert.append(movie)
                    fetched_movie_ids.add(movie_id)
                    pbar.update(1)

                # Be a good API citizen
                time.sleep(0.1)

            except requests.RequestException as e:
                print(f"Error fetching page {page}: {e}")
                time.sleep(5)  # Wait before retrying

    if movies_to_insert:
        print(f"\nFound {len(movies_to_insert)} new movies. Performing bulk insert...")
        db.bulk_insert_mappings(Movie, movies_to_insert)
        db.commit()
        print("Bulk insert complete.")
    else:
        print("\nNo new movies to add.")


def main():
    print("Starting metadata ingestion process...")
    Base.metadata.create_all(bind=engine)

    db = SessionLocal()
    try:
        fetch_popular_movies(db)
    finally:
        db.close()

    print("Metadata ingestion process finished.")


if __name__ == "__main__":
    main()
