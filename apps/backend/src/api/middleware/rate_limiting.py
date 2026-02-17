import time
from collections import defaultdict
from collections.abc import Awaitable, Callable
from typing import Any

from fastapi import Request, Response, status
from loguru import logger
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse


class RateLimitMiddleware(BaseHTTPMiddleware):
    """
    Simple in-memory fixed-window rate limiter.

    NOTE: In a multi-worker production environment, this should be
    replaced by a Redis-backed limiter.
    """

    def __init__(
        self,
        app: Any,
        limit: int = 5,
        window: int = 60,
        restricted_paths: list[str] | None = None,
    ):
        super().__init__(app)
        self.limit = limit
        self.window = window
        self.restricted_paths = restricted_paths or ["/jobs"]
        # In-memory store: { ip : [timestamps] }
        self.requests: dict[str, list[float]] = defaultdict(list)

    async def dispatch(
        self, request: Request, call_next: Callable[[Request], Awaitable[Response]]
    ) -> Response:
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
