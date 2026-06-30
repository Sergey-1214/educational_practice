from time import perf_counter

from fastapi import FastAPI, Request
from prometheus_client import Counter, Histogram
from prometheus_fastapi_instrumentator import Instrumentator


HTTP_REQUESTS_TOTAL = Counter(
    "app_http_requests_total",
    "Total number of HTTP requests handled by the application.",
    ("method", "path", "status_code"),
)

HTTP_REQUEST_DURATION_SECONDS = Histogram(
    "app_http_request_duration_seconds",
    "HTTP request duration in seconds.",
    ("method", "path"),
)


def setup_metrics(app: FastAPI) -> None:
    Instrumentator(excluded_handlers=["/metrics"]).instrument(app).expose(
        app,
        include_in_schema=False,
        endpoint="/metrics",
    )

    @app.middleware("http")
    async def collect_http_metrics(request: Request, call_next):  # type: ignore[no-untyped-def]
        started_at = perf_counter()
        path = request.url.path
        method = request.method
        status_code = "500"

        try:
            response = await call_next(request)
            status_code = str(response.status_code)
            return response
        finally:
            duration = perf_counter() - started_at
            HTTP_REQUESTS_TOTAL.labels(
                method=method,
                path=path,
                status_code=status_code,
            ).inc()
            HTTP_REQUEST_DURATION_SECONDS.labels(
                method=method,
                path=path,
            ).observe(duration)
