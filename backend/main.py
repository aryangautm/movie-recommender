from fastapi import FastAPI

app = FastAPI(
    title="Movie Recommender API",
    description="An API for a novel graph-based movie recommender system.",
    version="0.1.0",
)


@app.get("/")
def read_root():
    return {"message": "Welcome to the Movie Recommender API"}
