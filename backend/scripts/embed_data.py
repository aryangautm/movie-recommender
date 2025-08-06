from sentence_transformers import SentenceTransformer
from app.core.database import SessionLocal
from app.models.movie import Movie, MovieVisibility
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
                db.query(
                    Movie.id,
                    Movie.title,
                    Movie.release_year,
                    Movie.genres,
                    Movie.overview,
                    Movie.director,
                    Movie.cast,
                    Movie.ai_keywords,
                    Movie.additional_keywords,
                )
                .filter(
                    Movie.embedding.is_(None),
                    Movie.visibility == MovieVisibility.PUBLIC,
                    Movie.ai_keywords.is_not(None),
                    Movie.release_date < datetime.now().date(),
                )
                .all()
            )
        return movies
    except Exception as e:
        print(f"Error fetching movies for embedding: {e}")
        raise


def generate_embeddings(texts: List[str]):
    print("Generating embeddings for AI keywords...")
    model = SentenceTransformer("all-mpnet-base-v2")

    embeddings = model.encode(
        texts, convert_to_tensor=True, show_progress_bar=True
    ).tolist()

    return embeddings


def save_embeddings(movie_data: List[Dict]):
    with SessionLocal() as db:
        try:
            import json

            with open("backup_embeddings.json", "w") as f:
                json.dump(movie_data, f, indent=4)
            crud_movie.sync_bulk_patch_movies(db, movie_data)
            db.commit()
        except Exception as e:
            db.rollback()
            with open("error_log.txt", "a") as f:
                f.write(f"Error updating movie embeddings: {e}\n")
            raise


def get_movie_texts(movies: List[Movie]) -> List[str]:
    print("Building movie descriptions for embedding...")
    texts = []
    for movie in movies:
        desc = build_movie_description(
            movie.title,
            movie.release_year,
            [genre["name"] for genre in movie.genres],
            movie.overview,
            movie.director.get("name", None) if movie.director else None,
            [cast["name"] for cast in movie.cast],
            movie.ai_keywords + (movie.additional_keywords or []),
        )
        texts.append(desc)

    return texts


def build_movie_description(
    title: str,
    release_year: int,
    genres: List,
    overview: str,
    director: str,
    cast: List,
    keywords: List,
) -> str:

    truncated_overview = (
        " ".join(overview.strip().split()[:120]) + "..." if overview else ""
    )

    description_parts = []

    description_parts.append(
        f"{title} ({release_year}) is a {', '.join(genres).lower()} movie"
    )

    if director:
        description_parts.append(f" directed by {director}.")

    if cast:
        description_parts.append(f". Starring {', '.join(cast[:3])}.")

    if truncated_overview:
        description_parts.append(f". Plot summary: {truncated_overview}")

    if keywords:
        clean_keywords = [kw.replace(".", "").strip() for kw in keywords]
        description_parts.append(
            f". Key themes and narratives: {', '.join(clean_keywords)}."
        )

    return " ".join(description_parts)


if __name__ == "__main__":
    movies = get_movies()
    if not movies:
        print("No movies found for embedding.")
    else:
        movie_texts = get_movie_texts(movies)
        embeddings = generate_embeddings(movie_texts)

        if not len(embeddings) == len(movies):
            print(
                "Error: The number of generated embeddings does not match the number of movies."
            )
            print(
                f"Generated: {len(embeddings)}, Movies: {len(movies)}, and {len(movie_texts)} texts."
            )
            exit(1)

        embeddings_to_save = []
        for i, movie in enumerate(movies):
            movie_embeddings = {
                "id": movie.id,
                "embedding": embeddings[i],
            }
            embeddings_to_save.append(movie_embeddings)

        try:
            save_embeddings(embeddings_to_save)
        except Exception as e:
            print(f"Error saving embeddings")
            exit(1)
        print("All movie embeddings processed successfully.")
