from __future__ import annotations

import logging
import sys
import time
import uuid
from dataclasses import dataclass
from typing import Optional

from flask import Flask, g, request
from prometheus_client import Counter, Histogram, generate_latest, CONTENT_TYPE_LATEST


REQUEST_DURATION = Histogram(
    "concierge_request_duration_seconds",
    "HTTP request duration in seconds",
    ["method", "path", "status"],
    buckets=(
        0.05,
        0.1,
        0.2,
        0.5,
        1,
        2,
        5,
        10,
    ),
)
REQUEST_COUNT = Counter(
    "concierge_request_total",
    "Total HTTP requests",
    ["method", "path", "status"],
)


@dataclass
class ObservabilityConfig:
    requests_log_path: Optional[str] = None
    level: int = logging.INFO


def init_logging(config: ObservabilityConfig) -> logging.Logger:
    logger = logging.getLogger("concierge.request")
    logger.setLevel(config.level)
    if not logger.handlers:
        formatter = logging.Formatter(
            "%(asctime)s %(levelname)s %(message)s"
        )
        stream_handler = logging.StreamHandler(sys.stdout)
        stream_handler.setFormatter(formatter)
        logger.addHandler(stream_handler)
        if config.requests_log_path:
            file_handler = logging.FileHandler(config.requests_log_path)
            file_handler.setFormatter(formatter)
            logger.addHandler(file_handler)
    return logger


def setup_request_hooks(app: Flask, logger: logging.Logger) -> None:
    @app.before_request
    def _start_timer() -> None:
        g._req_start = time.perf_counter()
        g.request_id = uuid.uuid4().hex

    @app.after_request
    def _log_and_metrics(response):
        start = getattr(g, "_req_start", None)
        duration = (time.perf_counter() - start) if start else None
        duration_ms = duration * 1000 if duration is not None else None
        method = request.method
        path = request.path
        status = response.status_code

        REQUEST_COUNT.labels(method=method, path=path, status=status).inc()
        if duration is not None:
            REQUEST_DURATION.labels(method=method, path=path, status=status).observe(duration)

        logger.info(
            "request_id=%s method=%s path=%s status=%s duration_ms=%s",
            getattr(g, "request_id", ""),
            method,
            path,
            status,
            f"{duration_ms:.1f}" if duration_ms is not None else "n/a",
        )
        response.headers["X-Request-ID"] = getattr(g, "request_id", "")
        return response

    @app.route("/metrics")
    def metrics():
        return generate_latest(), 200, {"Content-Type": CONTENT_TYPE_LATEST}
