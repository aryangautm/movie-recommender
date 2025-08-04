from typing import List, Dict, Any
from app.core.config import settings
from pathlib import Path
from google import genai
from google.genai import types

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

    response = client.models.generate_content(
        model=model,
        contents=contents,
        config=generate_content_config,
    )
    response_str = response.text
    return response_str
