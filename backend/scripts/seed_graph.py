import os
import sys

import numpy as np
from neo4j import Driver, GraphDatabase, exceptions
from sentence_transformers import SentenceTransformer, util
from tqdm import tqdm

sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

from app.core.config import settings
from app.core.database import SessionLocal
from app.models.movie import Movie

MODEL_NAME = "all-MiniLM-L6-v2"
TOP_K = 20
RELATIONSHIP_BATCH_SIZE = 10000


def get_movies_from_postgres():
    print("Fetching movie data from PostgreSQL...")
    db = SessionLocal()
    try:
        movies = (
            db.query(Movie.id, Movie.overview).filter(Movie.overview.isnot(None)).all()
        )
        return {movie.id: movie.overview for movie in movies}
    finally:
        db.close()


def create_nodes_and_index(driver: Driver, movie_ids: list):
    print("Creating index on Movie nodes in Neo4j...")
    with driver.session() as session:
        session.run(
            "CREATE INDEX movie_id_index IF NOT EXISTS FOR (m:Movie) ON (m.tmdb_id)"
        )

    print(
        f"Creating {len(movie_ids)} movie nodes in Neo4j (if they don't already exist)..."
    )
    query = "UNWIND $ids AS movie_id MERGE (m:Movie {tmdb_id: movie_id})"
    with driver.session() as session:
        session.run(query, ids=movie_ids)


def generate_similarity_data(movie_data: dict) -> list:
    """
    Performs the AI-heavy part: generates embeddings and calculates similarities.
    Returns a list of relationship dictionaries.
    """
    print(f"Loading SentenceTransformer model: '{MODEL_NAME}'...")
    model = SentenceTransformer(MODEL_NAME)

    movie_ids = list(movie_data.keys())
    overviews = list(movie_data.values())

    print("Generating embeddings for all movie overviews...")
    embeddings = model.encode(overviews, convert_to_tensor=True, show_progress_bar=True)

    print("Computing similarity scores...")
    similarities = util.semantic_search(embeddings, embeddings, top_k=TOP_K + 1)

    print("Preparing relationship data...")
    relationships = []
    for i in tqdm(range(len(similarities)), desc="Formatting relationships"):
        source_movie_id = movie_ids[i]
        for sim_item in similarities[i]:
            if sim_item["corpus_id"] == i:
                continue

            target_movie_id = movie_ids[sim_item["corpus_id"]]
            score = round(sim_item["score"], 4)

            relationships.append(
                {"source": source_movie_id, "target": target_movie_id, "score": score}
            )
    return relationships


def batch_create_relationships(driver: Driver, relationships: list):
    """
    Creates similarity relationships in Neo4j in batches.
    """
    print(
        f"\nCreating {len(relationships)} similarity relationships in batches of {RELATIONSHIP_BATCH_SIZE}..."
    )
    query = """
    UNWIND $rels AS rel
    MATCH (a:Movie {tmdb_id: rel.source})
    MATCH (b:Movie {tmdb_id: rel.target})
    MERGE (a)-[r:IS_SIMILAR_TO]->(b)
    SET r.ai_score = rel.score, r.user_votes = 0
    """

    with tqdm(total=len(relationships), desc="Writing to Neo4j") as pbar:
        for i in range(0, len(relationships), RELATIONSHIP_BATCH_SIZE):
            batch = relationships[i : i + RELATIONSHIP_BATCH_SIZE]

            with driver.session() as session:
                try:
                    # An explicit transaction is automatically handled by session.run()
                    session.run(query, rels=batch, timeout=120)
                    pbar.update(len(batch))
                except exceptions.ServiceUnavailable as e:
                    print(
                        f"\nService unavailable during batch starting at index {i}. Error: {e}"
                    )
                    print(
                        "Please check Neo4j Aura status and network connection. Retrying may be necessary."
                    )
                    raise
                except Exception as e:
                    print(
                        f"\nAn unexpected error occurred during batch starting at index {i}. Error: {e}"
                    )
                    raise


def main():
    """The main orchestration function."""
    movie_data = get_movies_from_postgres()
    if not movie_data:
        print("No movies found in PostgreSQL. Please run 'ingest_metadata.py' first.")
        return

    # --- Step 1: Heavy AI processing (No DB connection needed) ---
    all_relationships = generate_similarity_data(movie_data)

    # --- Step 2: Connect to DB and perform write operations ---
    driver = None
    try:
        # We now connect to the DB *after* the heavy AI work is done.
        print("\nConnecting to Neo4j to write data...")
        driver = GraphDatabase.driver(
            settings.NEO4J_URI, auth=(settings.NEO4J_USER, settings.NEO4J_PASSWORD)
        )
        driver.verify_connectivity()
        print("Successfully connected to Neo4j.")

        # Ensure all nodes exist before creating relationships
        create_nodes_and_index(driver, list(movie_data.keys()))

        # Write relationships in manageable batches
        batch_create_relationships(driver, all_relationships)

    except exceptions.ServiceUnavailable as e:
        print(f"A critical Neo4j connection error occurred: {e}")
        print("Please check your network connection and Neo4j Aura status.")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
    finally:
        if driver:
            driver.close()
            print("\nNeo4j connection closed.")


if __name__ == "__main__":
    print("--- Starting AI-Powered Graph Seeding Process ---")
    main()
    print("--- Graph Seeding Process Finished ---")
