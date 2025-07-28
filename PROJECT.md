## Directory Structure
```
/backend
├── app/
│   ├── __init__.py
│   ├── api/
│   │   ├── __init__.py
│   │   └── v1/
│   │       ├── __init__.py
│   │       ├── routes.py
│   │       └── endpoints/
│   │           ├── __init__.py
│   │           ├── movies.py
│   │           └── votes.py
│   ├── core/
│   │   ├── __init__.py
│   │   ├── redis.py
│   │   ├── database.py
│   │   └── config.py
│   ├── crud/
│   │   ├── __init__.py
│   │   ├── crud_vote.py
│   │   └── crud_movie.py
│   ├── models/
│   │   ├── __init__.py
│   │   ├── vote.py
│   │   └── movie.py
│   ├── schemas/
│   │   ├── __init__.py
│   │   ├── vote.py
│   │   └── movie.py
│   ├── celery_worker.py
│   └── main.py
├── scripts/
│       ├── __init__.py
│       ├── seed_graph.py
│       └── ingest_metadata.py
├── .env
├── .env.example
└── requirements.txt
```
## Project Roadmap: Movie Recommender MVP

### **Phase 0: Foundation & Environment Setup**

**Goal:** Prepare the complete development environment and project structure. No application features are built here, but this phase is critical for a smooth development process.

*   **Step 1: Version Control & Project Structure**
    *   Initialize a Git repository.
    *   Create a monorepo structure:
        ```
        /project-root
          /backend
          /frontend
          .gitignore
          README.md
        ```

*   **Step 2: Tooling & Dependencies**
    *   **Backend:** Set up a Python virtual environment. Install FastAPI, Uvicorn, psycopg2-binary, neo4j, celery, redis.
    *   **Frontend:** Initialize a React application using Vite (recommended for speed) or Create React App.
    *   **Database:** Create a configuration file (`.env`) for database credentials.

*   **Step 3: Cloud Services Provisioning (Free Tiers)**
    *   Create an account on **TMDb** to get an API key.
    *   Set up a free-tier **Neo4j AuraDB** instance. Note the connection URI, username, and password.
    *   Set up a free-tier **PostgreSQL** database (e.g., via Supabase or Heroku). Note the connection string.
    *   Set up a free-tier **Redis** instance (e.g., via Redis Cloud or Heroku).

---

### **Phase 1: The Data Pipeline & Backend Core**

**Goal:** Ingest all necessary movie data and build the core graph structure. The backend will be able to answer questions, but there's no UI yet.

*   **Step 1: Metadata Ingestion**
    *   **Feature:** Create a standalone Python script (`ingest_metadata.py`).
    *   **Action:** This script will:
        1.  Connect to the TMDb API.
        2.  Fetch the top 50,000 movies (by popularity).
        3.  For each movie, extract `id`, `title`, `overview`, `release_year`, `poster_path`, and `genres`.
        4.  Connect to your PostgreSQL database and store this information in a `movies` table.

*   **Step 2: AI-Powered Graph Seeding**
    *   **Feature:** Create a second script (`seed_graph.py`).
    *   **Action:** This script will:
        1.  Fetch all movies from your PostgreSQL database.
        2.  For each movie, generate a semantic vector from its `overview` using a Sentence-BERT model.
        3.  Connect to your Neo4j instance.
        4.  Create a `(m:Movie {tmdb_id: ...})` node for each movie. Create an index on `tmdb_id` for fast lookups.
        5.  **Crucially:** For each movie, calculate the cosine similarity to all other movies. Find the top 20 most similar movies.
        6.  For each of these top 20 pairs, create a relationship in Neo4j:
            `MERGE (a:Movie {tmdb_id: id1}) MERGE (b:Movie {tmdb_id: id2}) MERGE (a)-[r:IS_SIMILAR_TO]->(b) SET r.ai_score = ..., r.user_votes = 0`

*   **Step 3: Core API Endpoints (Read-Only)**
    *   **Feature:** Build the main FastAPI application.
    *   **Action:** Create the following endpoints:
        *   `GET /search`: Takes a query parameter `q`. It will search the PostgreSQL `movies` table for titles and return a list of matching movies (ID, title, poster).
        *   `GET /movies/{tmdb_id}`: Returns the full metadata for a single movie from PostgreSQL.
        *   `GET /movies/{tmdb_id}/similar`: This is the star of the show. It will:
            1.  Query Neo4j for the given `tmdb_id`.
            2.  Find all movies connected by an `:IS_SIMILAR_TO` relationship.
            3.  Order them by `ai_score` descending.
            4.  Return a list of the top 20 similar movies, including their `ai_score` and `user_votes`.

---

### **Phase 2: The Frontend & Read-Only Experience**

**Goal:** Build a fully functional, beautiful user interface where users can search for movies and explore the AI-generated recommendations. This is the first **demonstrable milestone**.

*   **Step 1: Basic UI Components**
    *   **Feature:** Create reusable React components.
    *   **Action:** Build `SearchBar.js`, `MovieCard.js` (displays a poster and title), and `MovieList.js` (displays a grid of MovieCards).

*   **Step 2: Page Structure & Routing**
    *   **Feature:** Set up client-side routing.
    *   **Action:** Use `react-router-dom` to create two main pages:
        *   **HomePage (`/`):** Features the `SearchBar` prominently.
        *   **MoviePage (`/movie/:tmdb_id`):** Displays the details of a specific movie.

*   **Step 3: API Integration & State Management**
    *   **Feature:** Connect the frontend to the backend API.
    *   **Action:**
        1.  On the `HomePage`, the `SearchBar` will call the `/search` endpoint as the user types, displaying results.
        2.  On the `MoviePage`, use the `tmdb_id` from the URL to call `/movies/{tmdb_id}` for metadata and `/movies/{tmdb_id}/similar` for the recommendation list.
        3.  Manage loading and error states gracefully.

*   **Step 4: Implement "Psychological Priming"**
    *   **Feature:** Make the AI-generated graph feel alive.
    *   **Action:** In the similarity list component, display the vote count for each movie using the formula: `displayVotes = round(ai_score * 10) + user_votes`. Initially, this will just be the AI score, creating a sense of an existing consensus. Add a small "(AI-suggested)" label.

---

### **Phase 3: The Interactive Layer & Community Contribution**

**Goal:** Implement the anonymous voting system, transforming the app from a passive utility into an interactive, community-driven platform.

*   **Step 1: Backend Voting Infrastructure**
    *   **Feature:** Set up the asynchronous voting pipeline.
    *   **Action:**
        1.  Configure Celery in your FastAPI project to use your Redis instance as a message broker.
        2.  Create a background **Worker** process. This worker will contain a task function that takes two movie IDs, connects to Neo4j, and increments the `user_votes` on the corresponding edge.

*   **Step 2: Voting API Endpoint**
    *   **Feature:** Create the endpoint to receive votes.
    *   **Action:**
        1.  Create a `POST /vote` endpoint in FastAPI.
        2.  It will accept a request body containing `{ movie_id_1, movie_id_2, fingerprint }`.
        3.  This endpoint will **not** write to the database. It will only perform basic validation and then call the Celery task to run in the background. This ensures the API response is instant.

*   **Step 3: Frontend Voting UI & Logic**
    *   **Feature:** Allow users to cast votes.
    *   **Action:**
        1.  On the `MoviePage`, next to each movie in the similarity list, add a "Link as Similar" button.
        2.  Integrate a library like `fingerprintjs2` to generate a unique browser fingerprint for each user session.
        3.  When a user clicks the vote button, the frontend will:
            a. Send a request to the `POST /vote` endpoint with the two movie IDs and the browser fingerprint.
            b. On a successful response, provide immediate feedback: disable the button, change its text to "Voted!", and optimistically increment the vote count on the screen by one.

---

### **Phase 4: Polish, Deployment & Launch**

**Goal:** Optimize the application, deploy it to the cloud, and prepare for public launch.

*   **Step 1: Abuse Mitigation & Rate Limiting**
    *   **Feature:** Implement the basic abuse prevention we designed.
    *   **Action:**
        1.  The Worker service will use Redis to store fingerprints that have voted on a specific pair within the last 24 hours, rejecting duplicate votes.
        2.  Implement IP-based rate limiting on the `/vote` endpoint in FastAPI as a secondary defense.

*   **Step 2: Final UI/UX Polish**
    *   **Feature:** Ensure the application is polished and professional.
    *   **Action:** Add a simple "About" page explaining the philosophy. Add loading skeletons for a smoother feel. Ensure the mobile layout is responsive and usable. Add the "Get Notified" email capture form.

*   **Step 3: Optimization & Indexing**
    *   **Feature:** Make sure the app is fast.
    *   **Action:** Double-check that all necessary indexes are created in both PostgreSQL (`movies.title`) and Neo4j (`Movie(tmdb_id)`).

*   **Step 4: Deployment**
    *   **Feature:** Make the application live on the internet.
    *   **Action:**
        1.  Deploy the **React Frontend** to a static hosting provider like **Vercel** or **Netlify**.
        2.  Deploy the **FastAPI Backend** and the **Celery Worker** as two separate processes on a service like **Heroku** or AWS Elastic Beanstalk.
        3.  Configure all production environment variables (database URIs, API keys, etc.).

By following this roadmap, we will systematically build a robust and compelling MVP that perfectly showcases your unique vision for movie recommendations. Each phase delivers concrete value and moves us closer to a successful launch.