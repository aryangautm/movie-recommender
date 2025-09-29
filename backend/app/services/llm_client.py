import time
from pathlib import Path
from typing import Any, Dict, List

from google import genai
from google.genai import types

from app.core.config import settings
from app.utils import llm_parser

from .prompt import ai_keywords_prompt, multi_turn_rec_prompt

PROMPT_FILE = Path(__file__).parent / "rec_prompt.txt"

with open(PROMPT_FILE, "r", encoding="utf-8") as f:
    PROMPT_TXT = f.read().strip()


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


def multi_turn_rec(movie: Dict[str, Any], selected_keywords: List[str]):

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
        if movie.release_date.year >= 2023
        else []
    )
    generate_content_config = types.GenerateContentConfig(
        temperature=0.25,
        thinking_config=types.ThinkingConfig(
            thinking_budget=0,
        ),
        system_instruction=[
            types.Part.from_text(text=multi_turn_rec_prompt),
        ],
        tools=tools,
    )
    duplicate_movies = set()

    chat = client.chats.create(
        model=model,
        config=generate_content_config,
        history=contents,
    )
    for _ in range(6 // count):
        input_message = f"Recommend {count} different movies"

        if duplicate_movies:
            input_message += (
                f"\nshould not include any of these: {list(duplicate_movies)}"
            )

        start_ts = time.perf_counter()

        try:
            response = chat.send_message(input_message)

            sim_movies = llm_parser.parse_llm_recommendations(response.text)

            try:
                for movie in sim_movies["movies"]:
                    duplicate_movies.add(movie["title"])
            except:
                pass

        except:
            print("Error in parsing response")
            continue

        elapsed_ms = time.perf_counter() - start_ts
        print("Time to generate one batch", f"{elapsed_ms:.1f}", "seconds")

        yield sim_movies


def generate_keywords(title: str, release_year: int) -> str:
    client = genai.Client(
        api_key=settings.GEMINI_API_KEY,
    )

    USER_INPUT = f"Movie Title: {title}\nRelease Year: {release_year}"

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
        if release_year >= 2023
        else []
    )

    generate_content_config = types.GenerateContentConfig(
        temperature=0.4,
        thinking_config=types.ThinkingConfig(
            thinking_budget=0,
        ),
        system_instruction=[
            types.Part.from_text(text=ai_keywords_prompt),
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
    print("Time to generate keywords", f"{elapsed_ms:.1f}", "seconds")
    response_str = response.text
    keywords_json = llm_parser.parse_llm_keywords(response_str, "keywords")
    return keywords_json.get("keywords", [])
