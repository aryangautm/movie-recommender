from pydantic import BaseModel
from typing import List, Optional


class Genre(BaseModel):
    id: int
    name: str


class MovieBase(BaseModel):
    title: Optional[str] = None
    overview: Optional[str] = None
    release_year: Optional[int] = None
    poster_path: Optional[str] = None
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
    release_year: Optional[int]
    poster_path: Optional[str]


class SimilarMovie(Movie):
    ai_score: float
    user_votes: int
