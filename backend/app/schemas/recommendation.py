from pydantic import BaseModel, Field
from typing import List, Literal, Optional


class RecRequest(BaseModel):
    """The request body for the advanced similarity search."""

    source_movie_id: int = Field(
        ..., description="The TMDb ID of the movie the user liked."
    )
    selected_keywords: Optional[List[str]] = Field(
        [],
        description="A list of AI-generated keywords the user selected.",
    )


class BaseRecResult(BaseModel):
    id: int
    title: str
    overview: Optional[str] = ""
    release_year: int
    poster_path: str
    justification: Optional[List[str]] = Field(
        default_factory=list, description="Keywords that matched the source movie."
    )


class LLMRecResult(BaseRecResult):
    ai_score: float = Field(..., description="The LLM's assigned similarity score.")


class RecResponse(BaseModel):
    status: Literal["complete", "partial"] = Field(
        ..., description="`complete` if from cache, `partial` if a fallback."
    )
    results: List[BaseRecResult]
