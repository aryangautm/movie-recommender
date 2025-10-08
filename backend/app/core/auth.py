from fastapi import HTTPException, status, Security
from fastapi.security import APIKeyHeader
import secrets
from .config import settings

api_key_scheme = APIKeyHeader(name="X-API-Key", auto_error=False)


def require_api_key(key: str = Security(api_key_scheme)):
    if key is None or not secrets.compare_digest(key, settings.APP_AUTH_KEY):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing or invalid API key",
        )
    return "api-client"
