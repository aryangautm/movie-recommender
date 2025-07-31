import os
import sys
import math
import numpy as np
from tqdm import tqdm
from neo4j import Driver, GraphDatabase, exceptions
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import pairwise_distances
from sklearn.preprocessing import MultiLabelBinarizer

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


def get_movies_from_postgres():
    """Fetches all necessary movie data fields from PostgreSQL."""
    print("Fetching rich movie data from PostgreSQL...")
    db_gen = get_db()
    db = next(db_gen)
    try:
        # Fetch all fields required for the Movie DNA model
        return db.query(
            Movie.id,
            Movie.title,
            Movie.overview,
            Movie.genres,
            Movie.keywords,
            Movie.director,
            Movie.cast,
            Movie.collection,
            Movie.vote_count,
            Movie.vote_average,
        ).all()
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
    metadata_corpus = []  # For fitting the MultiLabelBinarizer

    # First pass: collect all metadata features to build a vocabulary
    print("Step 1/3: Building metadata vocabulary...")
    for movie in movies_raw:
        if not movie.overview:
            continue
        genres = (
            [g["name"] for g in movie.genres if g and "name" in g]
            if movie.genres
            else []
        )
        keywords = (
            [k["name"] for k in movie.keywords[:5] if k and "name" in k]
            if movie.keywords
            else []
        )
        director_name = (
            movie.director["name"]
            if movie.director and "name" in movie.director
            else ""
        )
        cast_names = (
            [c["name"] for c in movie.cast[:3] if c and "name" in c]
            if movie.cast
            else []
        )
        metadata_corpus.append(genres + keywords + [director_name] + cast_names)

    # Use MultiLabelBinarizer to create one-hot encoded vectors from metadata
    mlb = MultiLabelBinarizer()
    mlb.fit(metadata_corpus)

    # Second pass: generate the full profile for each movie
    print("Step 2/3: Generating DNA profiles for each movie...")
    for movie, metadata_features in tqdm(
        zip(movies_raw, metadata_corpus),
        total=len(movies_raw),
        desc="Processing Movie DNA",
    ):
        if not movie.overview:
            continue

        # 1. Create the rich semantic document for embedding
        director_name = (
            movie.director["name"]
            if movie.director and "name" in movie.director
            else ""
        )
        keyword_text = " ".join(
            [k["name"] for k in movie.keywords[:5] if k and "name" in k]
            if movie.keywords
            else []
        )
        rich_document = f"{movie.title}. Overview: {movie.overview} Keywords: {keyword_text}. Director: {director_name}."

        # 2. Generate vectors
        vector_semantic = model.encode(rich_document, convert_to_tensor=False)
        vector_metadata = mlb.transform([metadata_features])[0]

        # 3. Calculate Acclaim Score
        vote_avg = movie.vote_average if movie.vote_average else 0
        vote_count = movie.vote_count if movie.vote_count else 0
        score_acclaim = vote_avg * math.log10(vote_count + 1)  # +1 to avoid log10(0)

        movie_profiles[movie.id] = {
            "semantic": vector_semantic,
            "metadata": vector_metadata,
            "acclaim": score_acclaim,
        }

    print("Step 3/3: DNA processing complete.")
    return movie_profiles


def calculate_hybrid_similarities(profiles: dict, movies_raw: list):
    """
    Calculates the final similarity score using the hybrid model, including
    semantic, metadata, acclaim, and collection-based similarities.
    """
    print("Calculating hybrid similarity scores...")
    movie_ids = list(profiles.keys())

    # Extract DNA components into matrices for efficient, vectorized calculations
    semantic_vectors = np.array([p["semantic"] for p in profiles.values()])
    metadata_vectors = np.array(
        [p["metadata"] for p in profiles.values()], dtype=bool
    )  # Use boolean type for Jaccard
    acclaim_scores = np.array([p["acclaim"] for p in profiles.values()])

    # 1. Calculate semantic similarity (cosine)
    print("Calculating semantic similarities (cosine)...")
    semantic_sim_matrix = 1 - pairwise_distances(semantic_vectors, metric="cosine")

    # 2. Calculate metadata similarity (Jaccard for binary vectors)
    print("Calculating metadata similarities (Jaccard)...")
    # Note: `ensure_all_finite` is the new name for `force_all_finite` in scikit-learn >= 1.6
    metadata_sim_matrix = 1 - pairwise_distances(
        metadata_vectors, metric="jaccard", ensure_all_finite=False
    )

    # 3. Calculate acclaim penalty
    print("Calculating acclaim penalty...")
    min_acclaim, max_acclaim = np.min(acclaim_scores), np.max(acclaim_scores)
    norm_acclaim = (
        (acclaim_scores - min_acclaim) / (max_acclaim - min_acclaim)
        if max_acclaim > min_acclaim
        else np.zeros_like(acclaim_scores)
    )
    acclaim_diff_matrix = np.abs(norm_acclaim[:, np.newaxis] - norm_acclaim)
    acclaim_penalty_matrix = 1.0 - (
        0.1 * acclaim_diff_matrix
    )  # Max 10% penalty for different acclaim levels

    # 4. Combine scores into the final matrix
    print("Combining scores with hybrid model weights and penalties...")
    combined_sim_matrix = (W_SEMANTIC * semantic_sim_matrix) + (
        W_METADATA * metadata_sim_matrix
    )
    final_sim_matrix = combined_sim_matrix * acclaim_penalty_matrix

    # 5. Apply collection/franchise boost for explicit connections (Optimized)
    print("Applying collection/franchise boost (optimized)...")
    from collections import defaultdict

    movie_id_to_index = {id: i for i, id in enumerate(movie_ids)}
    collection_to_indices = defaultdict(list)

    for m in movies_raw:
        if m.collection and "id" in m.collection and m.id in movie_id_to_index:
            collection_id = m.collection["id"]
            movie_index = movie_id_to_index[m.id]
            collection_to_indices[collection_id].append(movie_index)

    boost = 0.5
    for collection_id, indices in collection_to_indices.items():
        if len(indices) > 1:
            for i in range(len(indices)):
                for j in range(i + 1, len(indices)):
                    idx1, idx2 = indices[i], indices[j]
                    # Apply boost and ensure score doesn't exceed 1.0
                    final_sim_matrix[idx1, idx2] = min(
                        1.0, final_sim_matrix[idx1, idx2] + boost
                    )
                    final_sim_matrix[idx2, idx1] = final_sim_matrix[idx1, idx2]

    # 6. Find top K for each movie and format for Neo4j
    print("Finding top K recommendations and formatting relationships...")
    relationships = []
    for i in tqdm(range(len(movie_ids)), desc="Formatting relationships"):
        sim_scores = final_sim_matrix[i]
        top_indices = np.argsort(sim_scores)[::-1][1 : TOP_K + 1]

        source_movie_id = movie_ids[i]
        for target_index in top_indices:
            target_movie_id = movie_ids[target_index]
            score = round(final_sim_matrix[i, target_index], 4)
            relationships.append(
                {"source": source_movie_id, "target": target_movie_id, "score": score}
            )

    return relationships


def create_nodes_and_index(driver: Driver, movie_ids: list):
    # ... (This function remains unchanged)
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
    # ... (This function remains unchanged)
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
                    session.run(query, rels=batch, timeout=120)
                    pbar.update(len(batch))
                except exceptions.ServiceUnavailable as e:
                    print(
                        f"\nService unavailable on batch starting at index {i}. Error: {e}. Aborting."
                    )
                    raise
                except Exception as e:
                    print(
                        f"\nAn error occurred on batch starting at index {a}. Error: {e}. Aborting."
                    )
                    raise


def main():
    """The main orchestration function."""
    movies_raw = get_movies_from_postgres()
    if not movies_raw:
        print("No movies found in PostgreSQL. Please run 'ingest_metadata.py' first.")
        return

    # Step 1: Perform all CPU/GPU intensive AI processing first.
    movie_profiles = preprocess_movies(movies_raw)
    all_relationships = calculate_hybrid_similarities(movie_profiles, movies_raw)

    # Step 2: Connect to the database and perform all write operations.
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
