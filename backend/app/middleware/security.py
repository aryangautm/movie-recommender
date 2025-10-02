import logging
import re
import time
from collections import defaultdict
from typing import Callable, Dict, List, Optional, Pattern, Set, Tuple

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse
from starlette.types import ASGIApp

logger = logging.getLogger(__name__)


class SecurityMiddleware(BaseHTTPMiddleware):
    """
    Production-grade security middleware to protect against common attacks.

    Features:
    - Blocks known vulnerability scanning paths
    - Rate limiting per IP address
    - Detection of suspicious request patterns
    - Configurable threat detection rules
    - Security event logging
    """

    def __init__(
        self,
        app: ASGIApp,
        *,
        enable_path_blocking: bool = True,
        enable_rate_limiting: bool = True,
        enable_pattern_detection: bool = True,
        rate_limit_requests: int = 100,  # Max requests per window
        rate_limit_window: int = 60,  # Time window in seconds
        suspicious_threshold: int = 5,  # Suspicious requests before blocking
        custom_blocked_paths: Optional[Set[str]] = None,
        custom_blocked_patterns: Optional[List[Pattern]] = None,
    ):
        super().__init__(app)
        self.enable_path_blocking = enable_path_blocking
        self.enable_rate_limiting = enable_rate_limiting
        self.enable_pattern_detection = enable_pattern_detection
        self.rate_limit_requests = rate_limit_requests
        self.rate_limit_window = rate_limit_window
        self.suspicious_threshold = suspicious_threshold

        # In-memory storage for rate limiting TODO: configure redis in production
        self._request_counts: Dict[str, List[float]] = defaultdict(list)
        self._suspicious_ips: Dict[str, int] = defaultdict(int)
        self._blocked_ips: Set[str] = set()

        # Known malicious paths to block
        self.blocked_paths = {
            # Git repository exposure
            "/.git/config",
            "/.git/HEAD",
            "/.git/index",
            "/.gitignore",
            # Environment files
            "/.env",
            "/.env.local",
            "/.env.production",
            "/.env.development",
            # WordPress/CMS
            "/wordpress/",
            "/wp-admin/",
            "/wp-login.php",
            "/wp-content/",
            "/wp-includes/",
            # Configuration files
            "/config.php",
            "/config.json",
            "/config.yml",
            "/configuration.php",
            # Database dumps
            "/backup.sql",
            "/database.sql",
            "/db.sql",
            "/dump.sql",
            # Admin panels
            "/admin/",
            "/administrator/",
            "/phpmyadmin/",
            "/phpMyAdmin/",
            "/adminer/",
            # Common CMS
            "/joomla/",
            "/drupal/",
            "/magento/",
            # Server files
            "/server-status",
            "/server-info",
            "/.htaccess",
            "/.htpasswd",
            "/web.config",
            # Backup files
            "/backup/",
            "/.backup",
            "/backups/",
            # Source code
            "/src.zip",
            "/source.zip",
            "/backup.zip",
            # Common vulnerabilities
            "/xmlrpc.php",
            "/readme.html",
            "/license.txt",
        }

        # Add custom blocked paths
        if custom_blocked_paths:
            self.blocked_paths.update(custom_blocked_paths)

        # Regex patterns for suspicious paths
        self.blocked_patterns = [
            re.compile(r"\.git(/|$)"),  # Any .git path
            re.compile(r"\.env"),  # Any .env file
            re.compile(r"\.sql$"),  # SQL dump files
            re.compile(r"\.zip$"),  # ZIP files (often used for backups)
            re.compile(r"\.tar\.gz$"),  # Compressed archives
            re.compile(r"/\.\."),  # Path traversal attempts
            re.compile(r"\.\./"),  # Path traversal attempts
            re.compile(r"wp-"),  # WordPress related
            re.compile(r"phpMyAdmin", re.IGNORECASE),  # phpMyAdmin
            re.compile(r"\.php$"),  # PHP files (if not a PHP app)
            re.compile(r"\.bak$"),  # Backup files
            re.compile(r"\.old$"),  # Old files
            re.compile(r"~$"),  # Backup files
            re.compile(r"/admin", re.IGNORECASE),  # Admin panels
            re.compile(r"\.config$"),  # Config files
        ]

        # Add custom patterns
        if custom_blocked_patterns:
            self.blocked_patterns.extend(custom_blocked_patterns)

        # Known vulnerability scanner patterns
        self.scanner_indicators = {
            # Swiss payment system files (not relevant for most apps)
            "/js/lkk_ch.js",
            "/js/twint_ch.js",
            "/css/support_parent.css",
        }

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Main security middleware dispatch method."""

        client_ip = self._get_client_ip(request)
        path = request.url.path

        # Check if IP is already blocked
        if client_ip in self._blocked_ips:
            logger.warning(f"Blocked request from banned IP: {client_ip} -> {path}")
            return self._security_response(
                "Access denied", status_code=403, client_ip=client_ip
            )

        # Check for blocked paths
        if self.enable_path_blocking:
            if self._is_blocked_path(path):
                logger.warning(
                    f"Security: Blocked malicious path attempt from {client_ip}: {path}"
                )
                self._record_suspicious_activity(client_ip)
                return self._security_response(
                    "Not found", status_code=404, client_ip=client_ip
                )

        # Check for scanner indicators
        if self.enable_pattern_detection:
            if self._is_scanner_request(path):
                logger.warning(f"Security: Scanner detected from {client_ip}: {path}")
                self._record_suspicious_activity(client_ip)
                return self._security_response(
                    "Not found", status_code=404, client_ip=client_ip
                )

        # Rate limiting
        if self.enable_rate_limiting:
            if not self._check_rate_limit(client_ip):
                logger.warning(f"Security: Rate limit exceeded for {client_ip}")
                return self._security_response(
                    "Too many requests",
                    status_code=429,
                    client_ip=client_ip,
                    retry_after=self.rate_limit_window,
                )

        # Request is safe, continue processing
        return await call_next(request)

    def _is_blocked_path(self, path: str) -> bool:
        """Check if path is in blocked list or matches blocked patterns."""
        # Check exact matches
        if path in self.blocked_paths:
            return True

        # Check regex patterns
        for pattern in self.blocked_patterns:
            if pattern.search(path):
                return True

        return False

    def _is_scanner_request(self, path: str) -> bool:
        """Detect if request looks like vulnerability scanning."""
        return path in self.scanner_indicators

    def _check_rate_limit(self, client_ip: str) -> bool:
        """Check if client IP has exceeded rate limit."""
        current_time = time.time()
        window_start = current_time - self.rate_limit_window

        # Get requests for this IP
        requests = self._request_counts[client_ip]

        # Remove old requests outside the window
        requests = [req_time for req_time in requests if req_time > window_start]
        self._request_counts[client_ip] = requests

        # Check if limit exceeded
        if len(requests) >= self.rate_limit_requests:
            self._record_suspicious_activity(client_ip)
            return False

        # Add current request
        requests.append(current_time)
        return True

    def _record_suspicious_activity(self, client_ip: str):
        """Record suspicious activity and block IP if threshold exceeded."""
        self._suspicious_ips[client_ip] += 1

        if self._suspicious_ips[client_ip] >= self.suspicious_threshold:
            self._blocked_ips.add(client_ip)
            logger.error(
                f"Security: IP {client_ip} blocked after {self._suspicious_ips[client_ip]} suspicious requests"
            )

    def _get_client_ip(self, request: Request) -> str:
        """Get the real client IP, handling proxy headers."""
        # Check common proxy headers
        proxy_headers = [
            "x-forwarded-for",
            "x-real-ip",
            "x-client-ip",
            "cf-connecting-ip",
        ]

        for header in proxy_headers:
            ip = request.headers.get(header)
            if ip:
                # x-forwarded-for can contain multiple IPs
                return ip.split(",")[0].strip()

        # Fallback to direct client IP
        if hasattr(request, "client") and request.client:
            return request.client.host

        return "unknown"

    def _security_response(
        self,
        message: str,
        status_code: int,
        client_ip: str,
        retry_after: Optional[int] = None,
    ) -> JSONResponse:
        """Generate a security-related response."""
        headers = {}
        if retry_after:
            headers["Retry-After"] = str(retry_after)

        # Return generic error to avoid information leakage
        return JSONResponse(
            status_code=status_code,
            content={"detail": message},
            headers=headers,
        )

    def get_blocked_ips(self) -> Set[str]:
        """Get list of currently blocked IPs (useful for monitoring)."""
        return self._blocked_ips.copy()

    def unblock_ip(self, ip: str) -> bool:
        """Manually unblock an IP address."""
        if ip in self._blocked_ips:
            self._blocked_ips.remove(ip)
            self._suspicious_ips.pop(ip, None)
            logger.info(f"Security: Manually unblocked IP {ip}")
            return True
        return False

    def get_suspicious_ips(self) -> Dict[str, int]:
        """Get list of IPs with suspicious activity count."""
        return dict(self._suspicious_ips)


def create_security_middleware(
    *,
    enable_all: bool = True,
    rate_limit_requests: int = 100,
    rate_limit_window: int = 60,
    suspicious_threshold: int = 5,
    custom_blocked_paths: Optional[Set[str]] = None,
) -> SecurityMiddleware:
    """
    Create a security middleware with production-ready defaults.

    Args:
        enable_all: Enable all security features
        rate_limit_requests: Maximum requests per window
        rate_limit_window: Time window in seconds
        suspicious_threshold: Number of suspicious requests before blocking IP
        custom_blocked_paths: Additional paths to block

    Returns:
        Configured SecurityMiddleware instance
    """
    return SecurityMiddleware(
        app=None,  # Will be set by FastAPI
        enable_path_blocking=enable_all,
        enable_rate_limiting=enable_all,
        enable_pattern_detection=enable_all,
        rate_limit_requests=rate_limit_requests,
        rate_limit_window=rate_limit_window,
        suspicious_threshold=suspicious_threshold,
        custom_blocked_paths=custom_blocked_paths,
    )
