Film Echo MVP README
Overview

Film Echo is an innovative, anonymous movie discovery platform that connects films based on similarities rather than traditional ratings. This MVP (Minimum Viable Product) serves as an "Anonymous Discovery Engine," focusing on AI-seeded graphs and community-driven voting to help users explore movies through relational links. It validates the core concept of rating-free discovery by allowing users to browse, vote on similarities, and receive transparent recommendations.

The platform emphasizes pure connections: no judgments, just mappings of what movies feel alike. Built with scalability in mind, it uses a hybrid database approach to handle movie metadata and similarity networks efficiently.
Key Features

    Movie Search and Autocomplete: Quickly find films using intuitive search with real-time suggestions.

    Movie Pages: Detailed views including metadata (title, release year, plot summary, poster), and a "Movies Like This" section showing similar films based on AI and user votes.

    Anonymous Voting: Users can suggest similarities with a simple "Link as similar?" button. Votes are limited via browser fingerprinting to prevent abuse without requiring accounts.

    Transparent Recommendations: Displays similarity sources (e.g., AI scores presented as initial "votes" to encourage community input).

    Browsable Clusters: Grouped movie collections, like "Inception with mind-bending thrillers," for endless exploration via clickable lists.

    Email Signup: Optional sign-up for updates on new features and releases.

    No User Accounts: Keeps it lightweight and privacy-focused for the MVP phase.

Tech Stack

This MVP is designed for lean development and easy deployment. Here's the breakdown:
Component	Technology	Purpose
Frontend	React	User interface for search, browsing, and voting.
Backend	FastAPI	API handling requests, voting, and graph queries.
Graph Database	Neo4j (AuraDB Free Tier)	Storing and querying movie similarity networks.
Metadata Database	PostgreSQL (Heroku Hobby Dev)	Holding static movie data from TMDb.
Caching	Redis	Fast access to popular queries and recommendations.
Task Queue	Celery with Redis	Asynchronous processing of votes.
Offline Processing	Python Scripts	Initial data pull from TMDb, vector creation with Sentence-BERT, and graph seeding.
Hosting	Heroku/AWS Fargate (Hobby/Basic) for backend; Vercel/Netlify (Free) for frontend.	
Installation and Setup
Prerequisites

    Python 3.8+

    Node.js 16+

    Accounts for: TMDb API, Neo4j AuraDB, PostgreSQL, Redis (or use managed services like Heroku).

    Install dependencies: pip install fastapi uvicorn celery redis sentence-transformers neo4j requests for backend; npm install for frontend.

Steps

    Clone the Repository:

text
git clone https://github.com/yourusername/film-echo-mvp.git
cd film-echo-mvp

Set Up Environment Variables:
Create a .env file with keys like:

    TMDB_API_KEY=your_tmdb_key

    NEO4J_URI=your_neo4j_uri

    NEO4J_USER=neo4j

    NEO4J_PASSWORD=your_password

    POSTGRES_URI=your_postgres_connection_string

    REDIS_URI=your_redis_uri

Offline Data Seeding:
Run Python scripts to populate the databases:

    text
    python scripts/pull_tmdb_data.py  # Fetches ~50k movies
    python scripts/generate_vectors.py  # Uses SBERT for similarity vectors
    python scripts/build_graph.py  # Seeds Neo4j with initial edges

    Install Dependencies:

        Backend: pip install -r requirements.txt

        Frontend: cd frontend && npm install

Running the Project

    Start the Backend:

text
celery -A tasks worker --loglevel=info  # Start worker for async tasks
uvicorn main:app --reload  # Run FastAPI server

Start the Frontend:

    text
    cd frontend
    npm start

    Access the App:
    Open http://localhost:3000 in your browser. For production, deploy to hosting services as noted in the tech stack.

The system uses fingerprinting (e.g., via fingerprintjs2) for anonymous vote limiting. Ensure Redis is running for caching and queues.
Usage

    Discover Movies: Search for a film, view its page, and explore "Movies Like This" lists.

    Vote on Similarities: On a movie page, search for another film and click "Link as similar?" to contribute anonymously.

    Browse Clusters: Click through recommendation lists to find new favorites based on community and AI links.

    Sign Up for Updates: Enter your email on the homepage for notifications.

This MVP focuses on core validation: user engagement with voting and discovery without logins.
Contributing

We welcome contributions to improve the MVP!

    Fork the repo and create a pull request.

    Focus areas: Bug fixes, UI enhancements, or expanding the AI seeding scripts.

    Follow the code style: Use PEP 8 for Python and ESLint for JavaScript.

    Test thoroughly, especially voting flows and graph queries.

For issues or suggestions, open a GitHub issue.
License

This project is licensed under the MIT License. See the LICENSE file for details.
