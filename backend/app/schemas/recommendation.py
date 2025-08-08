from pydantic import BaseModel, Field, field_serializer, field_validator
from typing import List, Literal, Optional
from app.utils.encryption import encrypt_id, decrypt_id


class RecRequest(BaseModel):
    """The request body for the advanced similarity search."""

    source_movie_id: str = Field(
        ..., description="The TMDb ID of the movie the user liked."
    )
    selected_keywords: Optional[List[str]] = Field(
        [],
        description="A list of AI-generated keywords the user selected.",
    )

    @field_validator("source_movie_id", mode="after")
    @classmethod
    def validate_id(cls, value: str) -> int:
        try:
            return decrypt_id(value)
        except Exception as e:
            raise ValueError(f"Invalid encrypted ID: {e}")


class BaseRecResult(BaseModel):
    id: int
    title: str
    overview: Optional[str] = ""
    release_year: int
    poster_path: str
    justification: Optional[List[str]] = Field(
        default_factory=list, description="Keywords that matched the source movie."
    )

    @field_serializer("id")
    def serialize_id(self, id: int) -> str:
        return encrypt_id(id)


class LLMRecResult(BaseRecResult):
    ai_score: float = Field(..., description="The LLM's assigned similarity score.")


class RecResponse(BaseModel):
    status: Literal["complete", "partial"] = Field(
        ..., description="`complete` if from cache, `partial` if a fallback."
    )
    results: List[BaseRecResult]
