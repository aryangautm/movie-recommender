from sentence_transformers import SentenceTransformer
from app.core.database import SessionLocal
from app.models.movie import Movie
from app.crud import crud_movie
from datetime import datetime
from typing import List, Dict


def get_movies():
    """Fetches all necessary movie data fields from PostgreSQL."""
    print("Fetching rich movie data from PostgreSQL...")
    try:
        movies = []
        with SessionLocal() as db:
            movies = (
                db.query(Movie.id, Movie.ai_keywords, Movie.additional_keywords)
                .filter(
                    Movie.embedding.is_(None),
                    Movie.ai_keywords.is_not(None),
                    Movie.release_date < datetime.now().date(),
                )
                .all()
            )
        return movies
    except Exception as e:
        print(f"Error fetching movies for embedding: {e}")
        raise


def generate_embeddings(movies_raw: list):
    print("Generating embeddings for AI keywords...")
    model = SentenceTransformer("all-MiniLM-L6-v2")

    movie_data = []

    texts = []
    for movie in movies_raw:
        text_part = (
            f"{' '.join(movie.ai_keywords)} {' '.join(movie.additional_keywords or [])}"
        )
        texts.append(text_part)

    embeddings = model.encode(
        texts, convert_to_tensor=True, show_progress_bar=True
    ).tolist()

    for i, movie in enumerate(movies_raw):
        movie_embeddings = {
            "id": movie.id,
            "embedding": embeddings[i],
        }
        movie_data.append(movie_embeddings)

    return movie_data


def save_embeddings(movie_data: List[Dict]):
    with SessionLocal() as db:
        try:
            crud_movie.sync_bulk_patch_movies(db, movie_data)
            db.commit()
        except Exception as e:
            print(f"Error updating movie embeddings: {e}")
            db.rollback()


if __name__ == "__main__":
    movies = get_movies()
    if not movies:
        print("No movies found for embedding.")
    else:
        movie_embeddings = generate_embeddings(movies)
        save_embeddings(movie_embeddings)
        print("All movie embeddings processed successfully.")
