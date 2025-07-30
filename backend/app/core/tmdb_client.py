import httpx
from typing import Optional, Dict, Any

from .config import settings

# Constants
TMDB_API_URL = "https://api.themoviedb.org/3"
REQUEST_TIMEOUT = 10  # seconds


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


# Create a single instance to be used across the application
tmdb_client = TMDbClient()
