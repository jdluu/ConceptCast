import time
from collections import defaultdict
from collections.abc import Awaitable, Callable
from typing import Any

from fastapi import Request, Response, status
from loguru import logger
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Provides in-memory fixed-window rate limiting for sensitive API paths.

    Prevents abuse of resource-intensive endpoints by restricting the number of
    requests allowed per IP address within a specified time window.
    """

    def __init__(
        self,
        app: Any,
        limit: int = 5,
        window: int = 60,
        restricted_paths: list[str] | None = None,
    ):
        """Initializes the rate limiting middleware.

        Args:
            app: The standard FastAPI application instance.
            limit: Maximum number of requests allowed per window.
            window: Duration of the rate limit window in seconds.
            restricted_paths: List of path prefixes that should be restricted.
        """
        super().__init__(app)
        self.limit = limit
        self.window = window
        self.restricted_paths = restricted_paths or ["/jobs"]
        self.requests: dict[str, list[float]] = defaultdict(list)

    async def dispatch(
        self, request: Request, call_next: Callable[[Request], Awaitable[Response]]
    ) -> Response:
        """Evaluates rate limits for incoming requests and enforces restrictions.

        Args:
            request: The incoming FastAPI request.
            call_next: The next handler in the execution pipeline.

        Returns:
            The original response or a JSONResponse with 429 status code.
        """
        # Only rate limit POST requests to restricted paths
        is_restricted = any(
            request.url.path.startswith(p) for p in self.restricted_paths
        )
        if request.method != "POST" or not is_restricted:
            return await call_next(request)

        client_ip = request.client.host if request.client else "unknown"
        now = time.time()

        # Clean old requests
        self.requests[client_ip] = [
            t for t in self.requests[client_ip] if now - t < self.window
        ]

        if len(self.requests[client_ip]) >= self.limit:
            logger.warning(
                f"Rate limit exceeded for IP: {client_ip} on {request.url.path}"
            )
            return JSONResponse(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                content={
                    "detail": (
                        "Too many requests. "
                        "Please wait a minute before creating another job."
                    ),
                    "retry_after": self.window,
                },
            )

        self.requests[client_ip].append(now)
        return await call_next(request)
