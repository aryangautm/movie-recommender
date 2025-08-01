from pydantic import BaseModel, Field


class VoteCreate(BaseModel):
    movie_id_1: int = Field(..., description="The TMDb ID of the first movie.")
    movie_id_2: int = Field(..., description="The TMDb ID of the second movie.")
    fingerprint: str = Field(
        ..., description="The unique browser fingerprint of the user."
    )


class VoteResponse(BaseModel):
    message: str
