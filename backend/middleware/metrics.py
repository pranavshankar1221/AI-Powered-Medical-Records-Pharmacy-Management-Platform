"""
Prometheus-compatible request instrumentation middleware.
"""

import time
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request


class MetricsMiddleware(BaseHTTPMiddleware):
    """Track request count, latency, and errors for Prometheus."""

    async def dispatch(self, request: Request, call_next):
        from routes.monitoring import increment_request, increment_error, add_latency

        start_time = time.time()
        increment_request()

        try:
            response = await call_next(request)
            duration = time.time() - start_time
            add_latency(duration)

            if response.status_code >= 400:
                increment_error()

            return response
        except Exception as e:
            increment_error()
            duration = time.time() - start_time
            add_latency(duration)
            raise
