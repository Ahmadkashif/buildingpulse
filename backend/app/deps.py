"""Process-wide telemetry and logging wiring.

Together with `app/main.py`, this module is the only permitted importer of
`opentelemetry` (enforced by the `otel-confined` import-linter contract).
Everything else stays framework-agnostic.

Three responsibilities:

1. `configure_telemetry()` installs an OpenTelemetry `TracerProvider` with a
   `ConsoleSpanExporter` (always on for dev visibility) and, when
   `OTEL_EXPORTER_OTLP_ENDPOINT` is set, an OTLP exporter for prod. It also
   activates auto-instrumentation for FastAPI, sqlite3, and outbound HTTPX.
2. `configure_logging()` points structlog at a JSON renderer with a
   processor chain that injects `request_id` (from a contextvar) and
   `trace_id` (from the active OpenTelemetry span) onto every record.
3. `RequestIdMiddleware` allocates a request_id per request, exposes it on
   the response as `X-Request-ID`, and binds it into the structlog context
   so every log line emitted while handling that request carries it.
"""

from __future__ import annotations

import logging
import os
import sys
import uuid
from collections.abc import Awaitable, Callable
from contextvars import ContextVar
from typing import Any

import structlog
from fastapi import FastAPI, Request, Response
from opentelemetry import trace
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.instrumentation.httpx import HTTPXClientInstrumentor
from opentelemetry.instrumentation.sqlite3 import SQLite3Instrumentor
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import (
    BatchSpanProcessor,
    ConsoleSpanExporter,
    SimpleSpanProcessor,
)
from starlette.middleware.base import BaseHTTPMiddleware

REQUEST_ID_HEADER = "X-Request-ID"
SERVICE_NAME = "buildingpulse-backend"

_request_id_var: ContextVar[str | None] = ContextVar("request_id", default=None)
_telemetry_configured = False
_logging_configured = False


def _add_request_id(_logger: Any, _name: str, event_dict: dict[str, Any]) -> dict[str, Any]:
    request_id = _request_id_var.get()
    event_dict["request_id"] = request_id if request_id is not None else ""
    return event_dict


def _add_trace_id(_logger: Any, _name: str, event_dict: dict[str, Any]) -> dict[str, Any]:
    span = trace.get_current_span()
    ctx = span.get_span_context() if span is not None else None
    if ctx is not None and ctx.is_valid:
        event_dict["trace_id"] = format(ctx.trace_id, "032x")
        event_dict["span_id"] = format(ctx.span_id, "016x")
    else:
        event_dict["trace_id"] = ""
    return event_dict


def configure_logging() -> None:
    """Wire structlog + stdlib logging to emit JSON with request_id + trace_id."""
    global _logging_configured
    if _logging_configured:
        return

    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=logging.INFO,
    )

    structlog.configure(
        processors=[
            structlog.contextvars.merge_contextvars,
            structlog.processors.add_log_level,
            structlog.processors.TimeStamper(fmt="iso"),
            _add_request_id,  # type: ignore[list-item]
            _add_trace_id,  # type: ignore[list-item]
            structlog.processors.JSONRenderer(),
        ],
        wrapper_class=structlog.make_filtering_bound_logger(logging.INFO),
        logger_factory=structlog.PrintLoggerFactory(file=sys.stdout),
        cache_logger_on_first_use=True,
    )
    _logging_configured = True


def configure_telemetry() -> None:
    """Install a TracerProvider with console + (optional) OTLP exporters."""
    global _telemetry_configured
    if _telemetry_configured:
        return

    provider = TracerProvider(resource=Resource.create({"service.name": SERVICE_NAME}))
    provider.add_span_processor(SimpleSpanProcessor(ConsoleSpanExporter()))

    otlp_endpoint = os.environ.get("OTEL_EXPORTER_OTLP_ENDPOINT")
    if otlp_endpoint:
        provider.add_span_processor(BatchSpanProcessor(OTLPSpanExporter(endpoint=otlp_endpoint)))

    trace.set_tracer_provider(provider)

    if not SQLite3Instrumentor().is_instrumented_by_opentelemetry:
        SQLite3Instrumentor().instrument()
    if not HTTPXClientInstrumentor().is_instrumented_by_opentelemetry:
        HTTPXClientInstrumentor().instrument()

    _telemetry_configured = True


def instrument_app(app: FastAPI) -> None:
    """Attach FastAPI HTTP-server auto-instrumentation to a specific app."""
    FastAPIInstrumentor.instrument_app(app)


class RequestIdMiddleware(BaseHTTPMiddleware):
    """Allocate a `request_id` per request, expose it as a header, and bind
    it into the structlog contextvars so every log line during the request
    carries the same id."""

    async def dispatch(
        self,
        request: Request,
        call_next: Callable[[Request], Awaitable[Response]],
    ) -> Response:
        incoming = request.headers.get(REQUEST_ID_HEADER)
        request_id = incoming if incoming else uuid.uuid4().hex
        token = _request_id_var.set(request_id)
        structlog.contextvars.bind_contextvars(request_id=request_id)
        log = structlog.get_logger("app.http")
        try:
            response = await call_next(request)
            log.info(
                "http.request",
                method=request.method,
                path=request.url.path,
                status=response.status_code,
            )
        finally:
            _request_id_var.reset(token)
            structlog.contextvars.unbind_contextvars("request_id")
        response.headers[REQUEST_ID_HEADER] = request_id
        return response


def get_logger(name: str | None = None) -> structlog.stdlib.BoundLogger:
    return structlog.get_logger(name) if name else structlog.get_logger()  # type: ignore[no-any-return]


__all__ = [
    "REQUEST_ID_HEADER",
    "RequestIdMiddleware",
    "configure_logging",
    "configure_telemetry",
    "get_logger",
    "instrument_app",
]
