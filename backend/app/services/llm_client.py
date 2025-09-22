from typing import List, Dict, Any
from app.core.config import settings
from pathlib import Path
from google import genai
from google.genai import types
import time

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
    yield response_str


MTR_FILE = Path(__file__).parent / "multi_turn_rec_prompt.txt"

with open(MTR_FILE, "r", encoding="utf-8") as f:
    MTR_TXT = f.read().strip()


def multi_turn_rec(movie: Dict[str, Any], selected_keywords: List[str]):
    client = genai.Client(
        api_key=settings.GEMINI_API_KEY,
    )
    count = 2

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
        if movie.release_date.year >= 2020
        else []
    )
    generate_content_config = types.GenerateContentConfig(
        temperature=0.25,
        thinking_config=types.ThinkingConfig(
            thinking_budget=0,
        ),
        system_instruction=[
            types.Part.from_text(text=MTR_TXT.format(count=count)),
        ],
        tools=tools,
    )

    chat = client.chats.create(
        model=model,
        config=generate_content_config,
        history=contents,
    )
    for i in range(6 / count):
        start_ts = time.perf_counter()
        response = chat.send_message(f"Recommend {count} more movies")
        elapsed_ms = time.perf_counter() - start_ts
        print("Time to generate one batch", f"{elapsed_ms:.1f}", "seconds")
        yield response.text
