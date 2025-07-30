from typing import List, Optional

from pydantic import BaseModel
from datetime import date


class Genre(BaseModel):
    id: int
    name: str


class MovieBase(BaseModel):
    title: Optional[str] = None
    overview: Optional[str] = None
    release_date: Optional[date] = None
    poster_path: Optional[str] = None
    backdrop_path: Optional[str] = None
    genres: Optional[List[Genre]] = []


class MovieCreate(MovieBase):
    id: int


class Movie(MovieBase):
    id: int

    class Config:
        from_attributes = True


class MovieSearchResult(BaseModel):
    id: int
    title: str
    overview: Optional[str] = None
    genres: List[Genre] = []
    release_date: Optional[date]
    backdrop_path: Optional[str]
    poster_path: Optional[str]


class SimilarMovie(Movie):
    ai_score: float
    user_votes: int


class TrendingMoviesPage(BaseModel):
    page: int
    results: List[Movie]  # We can reuse our existing Movie schema
    total_pages: int
    total_results: int
