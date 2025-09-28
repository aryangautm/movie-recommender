import re
from typing import List

from app.models.movie import Movie


def create_movie_desc(movie: Movie, keywords: List[str]) -> str:
    ai_keywords = movie.ai_keywords or []
    genres = [genre["name"] for genre in movie.genres or []]
    filtered_overview = filter_overview_by_keywords(movie.overview, keywords)

    description_parts = []
    emphasized_selected = ", ".join(keywords * 2)

    description_parts.append(
        f"Recommend movies emphasizing these specific themes and narratives: {emphasized_selected}."
    )
    # description_parts.append(f"Similar to plots involving: {filtered_overview}.")
    description_parts.append(f"In genres like {', '.join(genres[:2]).lower()}.")

    if ai_keywords:
        description_parts.append(
            f"With additional elements such as {', '.join(ai_keywords[:3])}."
        )

    return " ".join(description_parts)


def filter_overview_by_keywords(overview, selected_keywords):
    if not overview:
        return ""
    sentences = re.split(r"(?<!\w\.\w.)(?<![A-Z][a-z]\.)(?<=\.|\?)\s", overview.strip())
    filtered_sentences = [
        s for s in sentences if any(kw.lower() in s.lower() for kw in selected_keywords)
    ]
    return " ".join(filtered_sentences[:2])
