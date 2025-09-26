from typing import List, Dict, Any
from app.core.config import settings
from pydantic import BaseModel, Field
from pathlib import Path
from google import genai
from google.genai import types
import time
import json

PROMPT_FILE = Path(__file__).parent / "rec_prompt.txt"

with open(PROMPT_FILE, "r", encoding="utf-8") as f:
    PROMPT_TXT = f.read().strip()


class Movie(BaseModel):
    """A model representing a single movie."""

    movie_title: str = Field(
        ..., description="Full title of the movie without release year."
    )
    release_year: int = Field(..., description="The year the movie was released.")
    similarity_score: float = Field(
        ...,
        ge=0.0,  # ge = greater than or equal to
        le=10.0,  # le = less than or equal to
        description="A score indicating how similar this movie is to the source movie, ranging from 0.0 to 10.0.",
    )
    justification_keywords: List[str] = Field(
        ...,
        max_length=5,
        description="A list of keywords (2-3 words each) justifying why the movie is similar to the provided liked movie and their reason.",
    )


class SimilarMovies(BaseModel):
    """
    A model to hold a list of exactly 6 distinct movies similar to a source movie.
    """

    movies: List[Movie] = Field(
        ...,
        min_length=6,
        max_length=6,
        description="A list of 6 distinct movies similar to the source movie.",
    )


def generate_recommendations(
    movie: Dict[str, Any], selected_keywords: List[str]
) -> None:
    client = genai.Client(
        api_key=settings.GEMINI_API_KEY,
    )

    USER_INPUT = f"""
    **Liked Movie:**
    `{movie.title} ({movie.release_date.year})`

    **Full Keyword List:**
    `{movie.ai_keywords}`

    **Liked Keywords (Focus on these for recommendations):**
    `{selected_keywords}`
    """

    model = "gemini-2.5-flash"
    contents = [
        types.Content(
            role="user",
            parts=[
                types.Part.from_text(text=USER_INPUT),
            ],
        ),
    ]
    tools = [
        types.Tool(googleSearch=types.GoogleSearch()),
    ]
    generate_content_config = types.GenerateContentConfig(
        temperature=0.25,
        thinking_config=types.ThinkingConfig(
            thinking_budget=0,
        ),
        system_instruction=[
            types.Part.from_text(text=PROMPT_TXT),
        ],
        tools=tools,
    )

    start_ts = time.perf_counter()
    response = client.models.generate_content(
        model=model,
        contents=contents,
        config=generate_content_config,
    )
    elapsed_ms = time.perf_counter() - start_ts
    print("Time to generate one batch", f"{elapsed_ms:.1f}", "seconds")
    response_str = response.text
    return response_str


MTR_FILE = Path(__file__).parent / "multi_turn_rec_prompt.txt"

with open(MTR_FILE, "r", encoding="utf-8") as f:
    MTR_TXT = f.read().strip()


def multi_turn_rec(movie: Dict[str, Any], selected_keywords: List[str]):
    duplicate_movies = set()
    client = genai.Client(
        api_key=settings.GEMINI_API_KEY,
    )
    count = 6

    USER_INPUT = f"""
    **Liked Movie:**
    `{movie.title} ({movie.release_date.year})`

    **Full Keyword List:**
    `{movie.ai_keywords}`

    **Liked Keywords (Focus on these for recommendations):**
    `{selected_keywords}`

    **Strictly exclude these movies below***
    `{list(duplicate_movies)}`
    """

    model = "gemini-2.5-flash"
    contents = [
        types.Content(
            role="user",
            parts=[
                types.Part.from_text(text=USER_INPUT),
            ],
        ),
    ]
    tools = (
        [
            types.Tool(googleSearch=types.GoogleSearch()),
        ]
        if movie.release_date.year >= 2020
        else []
    )
    generate_content_config = types.GenerateContentConfig(
        response_schema=SimilarMovies,
        response_mime_type="application/json",
        temperature=0.25,
        thinking_config=types.ThinkingConfig(
            thinking_budget=0,
        ),
        system_instruction=[
            types.Part.from_text(text=MTR_TXT),
        ],
        tools=tools,
    )

    chat = client.chats.create(
        model=model,
        config=generate_content_config,
        history=contents,
    )
    for i in range(40 // count):
        start_ts = time.perf_counter()
        response = chat.send_message(f"Recommend {count} different movies")
        elapsed_ms = time.perf_counter() - start_ts
        print("Time to generate one batch", f"{elapsed_ms:.1f}", "seconds")
        response_json: SimilarMovies = response.parsed
        for movie in response_json.movies:
            duplicate_movies.add(movie.movie_title)
        yield response_json.model_dump()
    print(chat.get_history())
