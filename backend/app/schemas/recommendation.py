from pydantic import BaseModel, Field
from typing import List, Literal, Union
from .movie import MovieSearchResult
from datetime import date


class AdvancedRecommendationRequest(BaseModel):
    """The request body for the advanced similarity search."""

    source_movie_id: int = Field(
        ..., description="The TMDb ID of the movie the user liked."
    )
    selected_keywords: List[str] = Field(
        ...,
        min_length=1,
        description="A list of AI-generated keywords the user selected.",
    )


class RecommendationResponse(BaseModel):
    id: int
    title: str
    release_year: int
    poster_path: str
    score: float


class FallbackMovieResult(RecommendationResponse):
    overview: str


class LLMRecommendationResult(RecommendationResponse):
    justification: List[str] = Field(
        ..., description="The LLM's reason for the recommendation."
    )


class AdvancedRecommendationResponse(BaseModel):
    status: Literal["complete", "partial"] = Field(
        ..., description="`complete` if from cache, `partial` if a fallback."
    )
    results: Union[List[LLMRecommendationResult], List[FallbackMovieResult]]
