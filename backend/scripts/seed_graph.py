import sys
import os
import numpy as np
from tqdm import tqdm
from neo4j import GraphDatabase
from sentence_transformers import SentenceTransformer, util

sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

from app.core.config import settings
from app.core.database import SessionLocal
from app.models.movie import Movie

MODEL_NAME = "all-MiniLM-L6-v2"
TOP_K = 20  # Number of similar movies to find for each movie


def get_movies_from_postgres():
    """Fetches all movies from the PostgreSQL database."""
    print("Fetching movie data from PostgreSQL...")
    db = SessionLocal()
    try:
        movies = (
            db.query(Movie.id, Movie.overview).filter(Movie.overview.isnot(None)).all()
        )
        return {movie.id: movie.overview for movie in movies}
    finally:
        db.close()


def create_nodes_and_index(driver, movie_ids):
    """Creates movie nodes in Neo4j if they don't exist and ensures an index is present."""
    print("Creating index on Movie nodes in Neo4j...")
    with driver.session() as session:
        session.run(
            "CREATE INDEX movie_id_index IF NOT EXISTS FOR (m:Movie) ON (m.tmdb_id)"
        )

    print(
        f"Creating {len(movie_ids)} movie nodes in Neo4j (if they don't already exist)..."
    )
    query = """
    UNWIND $ids AS movie_id
    MERGE (m:Movie {tmdb_id: movie_id})
    """
    with driver.session() as session:
        session.run(query, ids=movie_ids)


def create_similarity_relationships(driver, movie_data):
    """Generates embeddings and creates similarity relationships in Neo4j."""
    print(
        f"Loading SentenceTransformer model: '{MODEL_NAME}' (this may download the model)..."
    )
    model = SentenceTransformer(MODEL_NAME)

    movie_ids = list(movie_data.keys())
    overviews = list(movie_data.values())

    print(
        "Generating embeddings for all movie overviews... (This can take a while, especially without a GPU)"
    )
    embeddings = model.encode(overviews, convert_to_tensor=True, show_progress_bar=True)

    print("Computing similarity scores and finding top K for all movies...")
    # util.semantic_search performs cosine similarity and finds the top_k for all embeddings at once
    # It returns a list of lists, where each inner list contains top_k dictionaries
    similarities = util.semantic_search(embeddings, embeddings, top_k=TOP_K + 1)

    print("Preparing relationships for batch insertion into Neo4j...")
    relationships = []
    for i, movie_sim in enumerate(tqdm(similarities, desc="Formatting relationships")):
        source_movie_id = movie_ids[i]
        for sim_item in movie_sim:
            # The first item is always the movie itself, so we skip it
            if sim_item["corpus_id"] == i:
                continue

            target_movie_id = movie_ids[sim_item["corpus_id"]]
            score = round(sim_item["score"], 4)

            relationships.append(
                {"source": source_movie_id, "target": target_movie_id, "score": score}
            )

    print(f"Creating {len(relationships)} similarity relationships in Neo4j...")
    # Once again, use UNWIND to batch create all relationships in one efficient query
    query = """
    UNWIND $rels AS rel
    MATCH (a:Movie {tmdb_id: rel.source})
    MATCH (b:Movie {tmdb_id: rel.target})
    MERGE (a)-[r:IS_SIMILAR_TO]->(b)
    SET r.ai_score = rel.score, r.user_votes = 0
    """
    with driver.session() as session:
        # This can be a long-running query, so we set a timeout
        session.run(query, rels=relationships, timeout=300)


def main():
    """The main orchestration function."""
    movie_data = get_movies_from_postgres()
    if not movie_data:
        print("No movies found in PostgreSQL. Please run 'ingest_metadata.py' first.")
        return

    try:
        driver = GraphDatabase.driver(
            settings.NEO4J_URI, auth=(settings.NEO4J_USER, settings.NEO4J_PASSWORD)
        )
        driver.verify_connectivity()
        print("Successfully connected to Neo4j.")

        create_nodes_and_index(driver, list(movie_data.keys()))
        create_similarity_relationships(driver, movie_data)

        driver.close()
    except Exception as e:
        print(f"An error occurred: {e}")


if __name__ == "__main__":
    print("--- Starting AI-Powered Graph Seeding Process ---")
    main()
    print("--- Graph Seeding Process Finished ---")
