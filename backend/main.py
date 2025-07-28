from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.core.graph import close_graph_connection, connect_to_graph
from backend.app.api.v1.endpoints import movies


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Manages the application's lifespan events. This is the modern replacement
    for on_event("startup") and on_event("shutdown").
    """
    connect_to_graph()
    yield
    close_graph_connection()


app = FastAPI(title="Movie Recommender API", lifespan=lifespan)

allowed_origins = [origin.strip() for origin in settings.CORS_ORIGINS.split(",")]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(movies.router, prefix="/api/v1", tags=["Movies"])


@app.get("/")
def read_root():
    return {"message": "Welcome to the Movie Recommender API"}
