import time
import uuid
from collections.abc import Awaitable, Callable

import structlog
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

logger = structlog.get_logger(__name__)


class LoggingMiddleware(BaseHTTPMiddleware):
    """
    Middleware for structured request logging and tracing.

    Assigns a unique X-Request-ID to every request and logs the
    method, path, status code, and latency with structured logs.
    """

    async def dispatch(
        self,
        request: Request,
        call_next: Callable[[Request], Awaitable[Response]],
    ) -> Response:
        """Intercepts HTTP requests for centralized logging and request ID injection.

        Args:
            request: The incoming FastAPI request.
            call_next: The next middleware or route handler in the pipeline.

        Returns:
            The processed response with added X-Request-ID header.
        """
        request_id = str(uuid.uuid4())
        request.state.request_id = request_id

        start_time = time.perf_counter()

        request_logger = logger.bind(request_id=request_id)
        request_logger.info(
            "request_start", method=request.method, path=request.url.path
        )

        try:
            response = await call_next(request)
        except Exception as e:
            process_time = (time.perf_counter() - start_time) * 1000
            request_logger.exception(
                "request_fail",
                method=request.method,
                path=request.url.path,
                latency_ms=round(process_time, 2),
                error=str(e),
            )
            raise

        process_time = (time.perf_counter() - start_time) * 1000
        request_logger.info(
            "request_end",
            method=request.method,
            path=request.url.path,
            status_code=response.status_code,
            latency_ms=round(process_time, 2),
        )

        # Inject Request ID into response headers
        response.headers["X-Request-ID"] = request_id
        return response
