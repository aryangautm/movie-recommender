<p align="center">
    <h1>Cineko: A Movie Recommender Beyond Ratings</h1>
</p>

<p align="center">
    <img src="https://img.shields.io/badge/Python-3.11+-blue.svg" alt="Python Version">
    <img src="https://img.shields.io/badge/Framework-FastAPI-green" alt="FastAPI">
    <img src="https://img.shields.io/badge/Graph-Neo4j-orange.svg" alt="Neo4j Version">
    <img src="https://img.shields.io/badge/license-Apache--2.0-lightgrey" alt="License">
</p>

GraphRecs is a modern movie recommendation engine built on a simple yet powerful philosophy: **ratings are flawed, but relationships are meaningful.** Instead of asking "Is this movie good?", we ask "What does this movie *feel* like?".

This project moves away from traditional star ratings and instead builds a dynamic graph network where movies are connected based on their contextual similarity. These connections are seeded by advanced AI and refined by community contributions, creating a recommendation system that understands nuance and personal taste.

---

## ✨ Core Features

*   **🧠 AI-Powered Similarity:** Utilizes Sentence-BERT models to understand the semantic meaning of movie plots, themes, and tone, creating a rich baseline of connections.
*   **🕸️ Graph-Based Network:** All movies and their relationships are stored in a Neo4j graph database, allowing for powerful and fast traversal to find "movies like this one."
*   **🚫 Rating-Free Philosophy:** No 5-star ratings. No thumbs up/down. Recommendations are discovered by exploring connections between movies you already know.
*   **🔗 Community-Driven Connections (V2):** The AI-seeded graph is designed to be augmented by user votes, allowing the community to collaboratively define what makes movies similar.
*   **🚀 Built for Scale:** A modern, modular architecture using FastAPI, PostgreSQL, and Neo4j, designed to be scalable, maintainable, and production-ready.

---

## 🛠️ Tech Stack & Architecture

The system is built with a decoupled, microservice-friendly approach.

| Component             | Technology                                                              | Purpose                                          |
| --------------------- | ----------------------------------------------------------------------- | ------------------------------------------------ |
| **Backend API**       | ![FastAPI](https://img.shields.io/badge/FastAPI-0?style=flat&logo=fastapi) | High-performance, asynchronous API service.      |
| **Relational Data**   | ![PostgreSQL](https://img.shields.io/badge/PostgreSQL-61DAFB?style=flat&logo=postgresql) | Stores static movie metadata (titles, overviews). |
| **Graph Data**        | ![Neo4j](https://img.shields.io/badge/Neo4j-white?style=flat&logo=neo4j) | Stores the core movie-similarity graph network.  |
| **AI / Embeddings**   | ![PyTorch](https://img.shields.io/badge/PyTorch-lightgrey?style=flat&logo=pytorch) `sentence-transformers` | Generates semantic vectors from movie text.      |
| **Async Tasks (V2)**  | ![Celery](https://img.shields.io/badge/Celery-37814A?style=flat&logo=celery) ![Redis](https://img.shields.io/badge/Redis-DC382D?style=flat&logo=redis) | Manages background jobs like voting updates.     |
| **Frontend (Planned)**| ![React](https://img.shields.io/badge/React-lightgrey?style=flat&logo=react) | The user interface for discovery.                |

### High-Level System Flow (MVP)

```
+----------------+      +------------------+      +------------------+
|      User      |----->|  FastAPI Backend |----->|  PostgreSQL DB   |
| (React Client) |      |   (API Logic)    |      | (Movie Metadata) |
+----------------+      +--------+---------+      +------------------+
                                 |
                                 |
                                 v
                         +------------------+
                         |   Neo4j Graph DB |
                         | (Similarity Edges) |
                         +------------------+
```

---

## 🚀 Getting Started

Follow these steps to get the backend running locally.

### Prerequisites

*   Python 3.10+
*   Docker (Recommended for databases) or local installations of PostgreSQL and Neo4j.
*   An API key from [The Movie Database (TMDb)](https://www.themoviedb.org/settings/api).

### 1. Clone the Repository

```bash
git clone https://github.com/aryangautm/movie-recommender.git
cd movie-recommender
```

### 2. Configure Environment

Navigate to the `backend` directory.

```bash
cd backend
```

Create a `.env` file by copying the example template.

```bash
cp .env.example .env
```

Now, edit `.env` and fill in your credentials for TMDb, PostgreSQL, and Neo4j.

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Populate the Databases

Run the ingestion scripts in the correct order.

**First, ingest metadata into PostgreSQL:**

```bash
python -m scripts.ingest_metadata
```

**Second, seed the AI similarity graph in Neo4j:**
*(This may take a while as it downloads the ML model and processes data.)*

```bash
python -m scripts.seed_graph
```

### 5. Run the API Server

```bash
uvicorn app.main:app --reload
```

The API will be available at `http://127.0.0.1:8000`. You can access the interactive documentation at `http://127.0.0.1:8000/docs`.

---

## 🗺️ Project Roadmap (Future Work)

The current version provides the core read-only recommendation engine. Future development will focus on:

-   [ ] **Phase 2: Frontend UI** - Building the complete React-based user interface.
-   [ ] **Phase 3: Interactive Voting** - Implementing anonymous and user-based voting to refine the graph.
-   [ ] **Phase 4: User Accounts & Profiles** - Allowing users to create "taste profiles" and get personalized recommendations.
-   [ ] **Phase 5: Advanced Moderation** - Building a trust score system to weigh community votes.

---

## 📜 License

This project is licensed under the Apache-2.0 License. See the `LICENSE` file for details.