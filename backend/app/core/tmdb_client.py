import httpx
from typing import Optional, Dict, Any
from functools import lru_cache
from .config import settings
import requests

# Constants
TMDB_API_URL = "https://api.themoviedb.org/3"
REQUEST_TIMEOUT = 10  # seconds


chars_to_remove = "·'.-" + '"' + "!@#$%^&*()_+=[]{}|;<>?,/\\`~"
translation_table = str.maketrans("", "", chars_to_remove)


class TMDbClient:
    """
    A client for interacting with The Movie Database (TMDb) API.
    """

    def __init__(self):
        self.base_url = TMDB_API_URL
        self.headers = {
            "accept": "application/json",
        }
        self.params = {"api_key": settings.TMDB_API_KEY}

    async def _make_request(
        self, client: httpx.AsyncClient, endpoint: str
    ) -> Optional[Dict[str, Any]]:
        """
        Internal method to perform an async GET request.
        Returns the JSON response dict or None on failure.
        """
        try:
            response = await client.get(
                f"{self.base_url}{endpoint}",
                headers=self.headers,
                params=self.params,
                timeout=REQUEST_TIMEOUT,
            )
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as e:
            # The API returned a 4xx or 5xx error
            print(f"HTTP error occurred: {e}")
            return None
        except httpx.RequestError as e:
            # A network-level error occurred (timeout, connection error, etc.)
            raise

    async def get_movie_images(
        self, movie_id: int, client: httpx.AsyncClient
    ) -> Optional[Dict[str, Any]]:
        """
        Fetches image data for a specific movie.
        """
        return await self._make_request(client, f"/movie/{movie_id}/images")

    async def get_genre_map(self) -> Dict[int, str]:
        """
        Fetches the genre ID to name mapping from TMDb.
        The result is cached in memory for the lifetime of the process.
        """
        print("Fetching genre map from TMDb API...")
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.base_url}/genre/movie/list", params=self.params
                )
                response.raise_for_status()
                genres = response.json().get("genres", [])
                return {genre["id"]: genre["name"] for genre in genres}
        except httpx.RequestError as e:
            print(f"An error occurred while requesting TMDb: {e}")
            return {}
        except httpx.HTTPStatusError as e:
            print(
                f"TMDb API returned an error: {e.response.status_code} - {e.response.text}"
            )
            return {}

    async def fetch_trending_from_tmdb(self, page: int = 1) -> Dict[str, Any]:
        """
        Fetches a page of trending movies from the TMDb API using an async client.
        """
        async with httpx.AsyncClient() as client:
            try:
                params = {**self.params, "language": "en-US", "page": page}
                response = await client.get(
                    f"{self.base_url}/trending/movie/day", params=params
                )
                response.raise_for_status()  # Will raise an exception for 4xx/5xx responses
                return response.json()
            except httpx.RequestError as e:
                print(f"An error occurred while requesting TMDb: {e}")
                return None
            except httpx.HTTPStatusError as e:
                print(
                    f"TMDb API returned an error: {e.response.status_code} - {e.response.text}"
                )
                return None

    def search_movie(
        self, query: str, release_year: Optional[int] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Searches for movies by title and fetches results from TMDb.
        """
        try:
            movie_data = None
            response_data = {}
            query = query.translate(translation_table).strip().lower()
            with httpx.Client() as client:
                params = {
                    **self.params,
                    "query": query,
                    "include_adult": False,
                    "year": release_year,
                }
                response = client.get(f"{self.base_url}/search/movie", params=params)
                response.raise_for_status()
                response_data = response.json()
            if response_data.get("results"):
                for result in response_data["results"]:
                    result_title = (
                        result["title"].translate(translation_table).strip().lower()
                    )
                    if result_title == query:
                        movie_data = result
                        break
            return movie_data
        except httpx.RequestError as e:
            print(f"An error occurred while searching for movies: {e}")
            return None


# Create a single instance to be used across the application
tmdb_client = TMDbClient()
