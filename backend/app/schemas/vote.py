from pydantic import BaseModel, Field, field_validator

from app.utils.encryption import decrypt_id


class VoteCreate(BaseModel):
    movie_id_1: str = Field(..., description="The TMDb ID of the first movie.")
    movie_id_2: str = Field(..., description="The TMDb ID of the second movie.")
    fingerprint: str = Field(
        ...,
        description="The unique browser fingerprint of the user.",
        examples=["a_unique_fingerprint_string_12345"],
    )

    class Config:
        from_attributes = True

    @field_validator("movie_id_1", mode="after")
    @classmethod
    def validate_movie_id_1(cls, value: str) -> int:
        try:
            return decrypt_id(value)
        except Exception as e:
            raise ValueError(f"Invalid encrypted ID: {e}")

    @field_validator("movie_id_2", mode="after")
    @classmethod
    def validate_movie_id_2(cls, value: str) -> int:
        try:
            return decrypt_id(value)
        except Exception as e:
            raise ValueError(f"Invalid encrypted ID: {e}")


class VoteResponse(BaseModel):
    message: str
