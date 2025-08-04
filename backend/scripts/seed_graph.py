import os
import sys
import math
import numpy as np
from tqdm import tqdm
from neo4j import Driver, GraphDatabase, exceptions
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import pairwise_distances
from sklearn.preprocessing import MultiLabelBinarizer
from app.utils.scoring import calculate_effective_score

# Add parent directory to path to allow imports from 'app'
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

from app.core.config import settings
from app.core.database import SessionLocal, get_db
from app.models.movie import Movie

# --- Model & Seeding Configuration ---
MODEL_NAME = "all-MiniLM-L6-v2"  # A fast and effective model for semantic search
TOP_K = 20  # Number of similar movies to link for each movie
RELATIONSHIP_BATCH_SIZE = 10000  # Batch size for Neo4j writes

# --- Hybrid Scoring Weights ---
# These weights determine the personality of our recommender.
W_SEMANTIC = 0.65  # Weight for plot, themes, and text content
W_METADATA = 0.35  # Weight for director, cast, genres, etc.
from datetime import datetime


def get_movies_from_postgres():
    """Fetches all necessary movie data fields from PostgreSQL."""
    print("Fetching rich movie data from PostgreSQL...")
    db_gen = get_db()
    db = next(db_gen)
    try:
        return (
            db.query(
                Movie.id,
                Movie.title,
                Movie.overview,
                Movie.genres,
                Movie.ai_keywords,
            )
            .filter(Movie.release_date < datetime.now().date())
            .all()
        )
    finally:
        db.close()


def preprocess_movies(movies_raw: list):
    """
    Takes raw movie data and generates the 'Movie DNA' for each.
    This includes semantic vectors, metadata vectors, and acclaim scores.
    """
    print("Preprocessing movie data to create 'Movie DNA' profiles...")
    model = SentenceTransformer(MODEL_NAME)

    movie_profiles = {}
    metadata_corpus = []

    print("Step 1/3: Building metadata vocabulary...")
    for movie in movies_raw:
        if not movie.overview:
            continue
        genres = (
            [g["name"] for g in movie.genres if g and "name" in g]
            if movie.genres
            else []
        )
        keywords = movie.ai_keywords or []
        metadata_corpus.append(genres + keywords)

    mlb = MultiLabelBinarizer()
    mlb.fit(metadata_corpus)

    print("Step 2/3: Generating DNA profiles for each movie...")
    for movie, metadata_features in tqdm(
        zip(movies_raw, metadata_corpus),
        total=len(movies_raw),
        desc="Processing Movie DNA",
    ):
        if not movie.overview:
            continue

        keyword_text = " ".join(movie.ai_keywords if movie.ai_keywords else [])
        rich_document = f"Overview: {movie.overview} Keywords: {keyword_text}"

        vector_semantic = model.encode(rich_document, convert_to_tensor=False)
        vector_metadata = mlb.transform([metadata_features])[0]

        movie_profiles[movie.id] = {
            "semantic": vector_semantic,
            "metadata": vector_metadata,
        }

    print("DNA processing complete.")
    return movie_profiles


def calculate_hybrid_similarities(profiles: dict, movies_raw: list):
    print("Calculating hybrid similarity scores...")
    movie_ids = list(profiles.keys())

    semantic_vectors = np.array([p["semantic"] for p in profiles.values()])

    print("Calculating semantic similarities (cosine)...")
    semantic_sim_matrix = 1 - pairwise_distances(semantic_vectors, metric="cosine")

    print("Combining scores with hybrid model weights and penalties...")
    final_sim_matrix = semantic_sim_matrix

    print("Finding top K recommendations and formatting relationships...")
    relationships = []
    for i in tqdm(range(len(movie_ids)), desc="Formatting relationships"):
        sim_scores = final_sim_matrix[i]
        top_indices = np.argsort(sim_scores)[::-1][1 : TOP_K + 1]

        source_movie_id = movie_ids[i]
        for target_index in top_indices:
            target_movie_id = movie_ids[target_index]
            hybrid_similarity_score = round(final_sim_matrix[i, target_index], 4)
            initial_effective_score = calculate_effective_score(
                user_votes=0, ai_score=None, similarity_score=hybrid_similarity_score
            )
            relationships.append(
                {
                    "source": source_movie_id,
                    "target": target_movie_id,
                    "similarity_score": hybrid_similarity_score,
                    "effective_score": initial_effective_score,
                }
            )

    return relationships


def create_nodes_and_index(driver: Driver, movie_ids: list):
    print("Creating index on Movie nodes in Neo4j...")
    with driver.session() as session:
        session.run(
            "CREATE INDEX movie_id_index IF NOT EXISTS FOR (m:Movie) ON (m.tmdb_id)"
        )
    print(
        f"Creating {len(movie_ids)} movie nodes in Neo4j (if they don't already exist)..."
    )
    with driver.session() as session:
        session.run(
            "UNWIND $ids AS movie_id MERGE (m:Movie {tmdb_id: movie_id})", ids=movie_ids
        )


def batch_create_relationships(driver: Driver, relationships: list):
    print(
        f"\nCreating {len(relationships)} similarity relationships in batches of {RELATIONSHIP_BATCH_SIZE}..."
    )
    query = """
    UNWIND $rels AS rel
    MATCH (a:Movie {tmdb_id: rel.source})
    MATCH (b:Movie {tmdb_id: rel.target})
    MERGE (a)-[r:IS_SIMILAR_TO]->(b)
    SET 
        r.similarity_score = rel.similarity_score,
        r.ai_score = null,
        r.user_votes = 0,
        r.effective_score = rel.effective_score
    """
    with tqdm(total=len(relationships), desc="Writing to Neo4j") as pbar:
        for i in range(0, len(relationships), RELATIONSHIP_BATCH_SIZE):
            batch = relationships[i : i + RELATIONSHIP_BATCH_SIZE]
            with driver.session() as session:
                try:
                    session.run(query, rels=batch, timeout=120)
                    pbar.update(len(batch))
                except exceptions.ServiceUnavailable as e:
                    print(
                        f"\nService unavailable on batch starting at index {i}. Error: {e}. Aborting."
                    )
                    raise
                except Exception as e:
                    print(
                        f"\nAn error occurred on batch starting at index {i}. Error: {e}. Aborting."
                    )
                    raise


def main():
    """The main orchestration function."""
    movies_raw = get_movies_from_postgres()
    if not movies_raw:
        print("No movies found in PostgreSQL. Please run 'ingest_metadata.py' first.")
        return

    movie_profiles = preprocess_movies(movies_raw)
    all_relationships = calculate_hybrid_similarities(movie_profiles, movies_raw)

    driver = None
    try:
        print("\nConnecting to Neo4j to write data...")
        driver = GraphDatabase.driver(
            settings.NEO4J_URI, auth=(settings.NEO4J_USER, settings.NEO4J_PASSWORD)
        )
        driver.verify_connectivity()
        print("Successfully connected to Neo4j.")

        movie_ids = [movie.id for movie in movies_raw]
        create_nodes_and_index(driver, movie_ids)
        batch_create_relationships(driver, all_relationships)

    except exceptions.ServiceUnavailable as e:
        print(f"A critical Neo4j connection error occurred: {e}")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
    finally:
        if driver:
            driver.close()
            print("\nNeo4j connection closed.")


if __name__ == "__main__":
    print("--- Starting AI-Powered Graph Seeding Process with Hybrid Model ---")
    main()
    print("--- Graph Seeding Process Finished ---")
