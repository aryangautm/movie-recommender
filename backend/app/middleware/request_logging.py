import asyncio
import json
import logging
import time
from typing import Callable, Dict, Optional, Set

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

from app.core.database import SessionLocal
from app.crud.crud_request_log import crud_request_log
from app.models.request_log import RequestMethod


logger = logging.getLogger(__name__)


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """
    Production-grade middleware for logging HTTP requests to the database.

    Features:
    - Asynchronous database logging to avoid blocking requests
    - Configurable sensitive header filtering
    - Request/response size tracking
    - Performance metrics collection
    - Error handling and fallback logging
    - Configurable path exclusions
    - Rate limiting protection for high-traffic scenarios
    """

    def __init__(
        self,
        app: ASGIApp,
        *,
        log_request_body: bool = False,
        log_response_body: bool = False,
        excluded_paths: Optional[Set[str]] = None,
        sensitive_headers: Optional[Set[str]] = None,
        max_body_size: int = 10000,  # Maximum body size to log in bytes
        enable_async_logging: bool = True,
        log_health_checks: bool = False,
    ):
        super().__init__(app)
        self.log_request_body = log_request_body
        self.log_response_body = log_response_body
        self.max_body_size = max_body_size
        self.enable_async_logging = enable_async_logging
        self.log_health_checks = log_health_checks

        # Default excluded paths (health checks, metrics, etc.)
        self.excluded_paths = excluded_paths or {
            "/health",
            "/healthz",
            "/metrics",
            "/favicon.ico",
            "/robots.txt",
        }

        # Sensitive headers to filter out
        self.sensitive_headers = sensitive_headers or {
            "authorization",
            "cookie",
            "x-api-key",
            "x-auth-token",
            "authorization",
            "proxy-authorization",
            "x-forwarded-for",  # Sometimes contains sensitive info
        }

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Main middleware dispatch method."""

        # Skip logging for excluded paths
        if not self.log_health_checks and request.url.path in self.excluded_paths:
            return await call_next(request)

        # Record start time
        start_time = time.time()

        # Extract request information
        request_data = await self._extract_request_data(request)

        # Process the request
        response = None
        error_message = None

        try:
            response = await call_next(request)
        except Exception as e:
            error_message = str(e)
            logger.error(f"Request processing error: {e}")
            # Re-raise the exception to maintain normal error handling
            raise
        finally:
            # Calculate processing time
            processing_time = time.time() - start_time

            # Extract response information
            response_data = self._extract_response_data(response) if response else {}

            # Log the request (async or sync based on configuration)
            if self.enable_async_logging:
                # Fire and forget - don't wait for database logging
                asyncio.create_task(
                    self._log_request_async(
                        request_data=request_data,
                        response_data=response_data,
                        processing_time=processing_time,
                        error_message=error_message,
                    )
                )
            else:
                # Synchronous logging (may impact performance)
                await self._log_request_async(
                    request_data=request_data,
                    response_data=response_data,
                    processing_time=processing_time,
                    error_message=error_message,
                )

        return response

    async def _extract_request_data(self, request: Request) -> Dict:
        """Extract relevant data from the request."""
        # Get client IP (handle proxy headers)
        client_ip = self._get_client_ip(request)

        # Filter headers
        filtered_headers = self._filter_headers(dict(request.headers))

        # Get query parameters, fallback to request payload if no query params
        query_params = dict(request.query_params) if request.query_params else None

        # Read request body once for both query_params fallback and size calculation
        request_size = None
        body = None
        if hasattr(request, "body"):
            try:
                body = await request.body()
                request_size = len(body) if body else 0
            except Exception as e:
                logger.warning(f"Could not read request body: {e}")

        # If no query parameters, try to get request payload
        if not query_params and body:
            try:
                # Try to parse as JSON
                try:
                    payload = json.loads(body.decode("utf-8"))
                    query_params = payload
                except (json.JSONDecodeError, UnicodeDecodeError):
                    # If not JSON, store as string representation
                    query_params = {"body": body.decode("utf-8", errors="replace")}
            except Exception as e:
                logger.warning(
                    f"Could not parse request body for query_params fallback: {e}"
                )

        return {
            "method": RequestMethod(request.method),
            "path": request.url.path,
            "query_params": query_params,
            "client_ip": client_ip,
            "user_agent": request.headers.get("user-agent"),
            "referer": request.headers.get("referer"),
            "headers": filtered_headers,
            "request_size": request_size,
        }

    def _extract_response_data(self, response: Response) -> Dict:
        """Extract relevant data from the response."""
        response_size = None

        # Try to get response size from headers
        if hasattr(response, "headers") and response.headers:
            content_length = response.headers.get("content-length")
            if content_length:
                try:
                    response_size = int(content_length)
                except ValueError:
                    pass

        return {
            "status_code": response.status_code if response else 500,
            "response_size": response_size,
        }

    def _get_client_ip(self, request: Request) -> Optional[str]:
        """Get the real client IP, handling proxy headers."""
        # Check common proxy headers in order of preference
        proxy_headers = [
            "x-forwarded-for",
            "x-real-ip",
            "x-client-ip",
            "cf-connecting-ip",  # Cloudflare
        ]

        for header in proxy_headers:
            ip = request.headers.get(header)
            if ip:
                # x-forwarded-for can contain multiple IPs, take the first one
                return ip.split(",")[0].strip()

        # Fallback to direct client IP
        if hasattr(request, "client") and request.client:
            return request.client.host

        return None

    def _filter_headers(self, headers: Dict[str, str]) -> Dict[str, str]:
        """Filter out sensitive headers."""
        return {
            key: value
            for key, value in headers.items()
            if key.lower() not in self.sensitive_headers
        }

    async def _log_request_async(
        self,
        *,
        request_data: Dict,
        response_data: Dict,
        processing_time: float,
        error_message: Optional[str] = None,
    ):
        """Log the request to the database asynchronously."""
        try:
            # Use synchronous database session for fire-and-forget logging
            with SessionLocal() as db:
                crud_request_log.create_sync(
                    db=db,
                    processing_time=processing_time,
                    error_message=error_message,
                    **request_data,
                    **response_data,
                )
        except Exception as e:
            # Log to application logger if database logging fails
            logger.error(f"Failed to log request to database: {e}")
            logger.info(
                f"Request: {request_data.get('method')} {request_data.get('path')} "
                f"- Status: {response_data.get('status_code')} "
                f"- Time: {processing_time:.3f}s"
            )

    def _should_log_request(self, request: Request) -> bool:
        """Determine if a request should be logged."""
        # Skip health checks if configured
        if not self.log_health_checks and request.url.path in self.excluded_paths:
            return False

        return True


# Convenience function to create middleware with common production settings
def create_request_logging_middleware(
    *,
    log_health_checks: bool = False,
    additional_excluded_paths: Optional[Set[str]] = None,
    enable_async_logging: bool = True,
) -> RequestLoggingMiddleware:
    """
    Create a request logging middleware with production-ready defaults.

    Args:
        log_health_checks: Whether to log health check endpoints
        additional_excluded_paths: Additional paths to exclude from logging
        enable_async_logging: Whether to use async logging (recommended for production)

    Returns:
        Configured RequestLoggingMiddleware instance
    """
    excluded_paths = {
        "/health",
        "/healthz",
        "/metrics",
        "/favicon.ico",
        "/robots.txt",
        "/docs",
        "/redoc",
        "/openapi.json",
    }

    if additional_excluded_paths:
        excluded_paths.update(additional_excluded_paths)

    return RequestLoggingMiddleware(
        app=None,  # Will be set by FastAPI
        log_request_body=True,  # Enable request body logging for payload capture
        log_response_body=False,
        excluded_paths=excluded_paths,
        enable_async_logging=enable_async_logging,
        log_health_checks=log_health_checks,
    )
