from typing import List, Optional, Any

from pydantic import BaseModel, Field, field_serializer
from datetime import date
from app.utils.encryption import encrypt_id


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

    @field_serializer("id")
    def serialize_id(self, id: int) -> str:
        print(f"Encrypting ID: {id}")
        return encrypt_id(id)


class MovieSearchResult(BaseModel):
    id: int
    title: str
    overview: Optional[str] = None
    genres: List[Genre] = []
    release_date: Optional[date]
    backdrop_path: Optional[str]
    poster_path: Optional[str]
    ai_keywords: Optional[List[Any]] = Field(alias="keywords")
    tagline: Optional[str] = None

    class Config:
        from_attributes = True
        populate_by_name = True

    @field_serializer("id")
    def serialize_id(self, id: int) -> str:
        print(f"Encrypting ID: {id}")
        return encrypt_id(id)


class SimilarMovie(Movie):
    ai_score: float
    user_votes: int


class TrendingMoviesPage(BaseModel):
    page: int
    results: List[Movie]  # We can reuse our existing Movie schema
    total_pages: int
    total_results: int
