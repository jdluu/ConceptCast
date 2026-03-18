import time
import uuid
from collections.abc import Awaitable, Callable

from fastapi import Request, Response
from loguru import logger
from starlette.middleware.base import BaseHTTPMiddleware


class LoggingMiddleware(BaseHTTPMiddleware):
    """
    Middleware for structured request logging and tracing.

    Assigns a unique X-Request-ID to every request and logs the
    method, path, status code, and latency using loguru.
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

        # Add context to all loguru logs in this task
        with logger.contextualize(request_id=request_id):
            logger.info(f"REQ START: {request.method} {request.url.path}")

            try:
                response = await call_next(request)
            except Exception as e:
                process_time = (time.perf_counter() - start_time) * 1000
                logger.error(
                    f"REQ FAIL: {request.method} {request.url.path} - "
                    f"Error: {e} - Latency: {process_time:.2f}ms"
                )
                raise

            process_time = (time.perf_counter() - start_time) * 1000

            # Log completion
            logger.info(
                f"REQ END: {request.method} {request.url.path} "
                f"Status: {response.status_code} "
                f"Latency: {process_time:.2f}ms"
            )

            # Inject Request ID into response headers
            response.headers["X-Request-ID"] = request_id
            return response
