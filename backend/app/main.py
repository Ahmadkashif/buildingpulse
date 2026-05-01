"""FastAPI application factory.

The app composes the v1 controllers under `/api`. CORS is locked to the
local frontend dev origin; production origins land in a later phase.
On startup, the lifespan hook applies any pending SQL migrations.

Telemetry (OpenTelemetry tracing + structlog JSON logging) is wired here
via `app.deps`. Together with `app/deps.py`, this module is the only
permitted importer of `opentelemetry` (see the `otel-confined` contract).
"""

from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1.predictions import router as predictions_router
from app.deps import (
    RequestIdMiddleware,
    configure_logging,
    configure_telemetry,
    get_logger,
    instrument_app,
)
from app.repos.connection import connect
from app.repos.migrations import run_migrations

configure_logging()
configure_telemetry()


@asynccontextmanager
async def lifespan(_app: FastAPI) -> AsyncIterator[None]:
    log = get_logger("app.main")
    conn = connect()
    try:
        run_migrations(conn)
        log.info("startup.migrations_applied")
    finally:
        conn.close()
    yield


app = FastAPI(title="BuildingPulse API", version="0.1.0", lifespan=lifespan)

app.add_middleware(RequestIdMiddleware)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

instrument_app(app)

app.include_router(predictions_router, prefix="/api")

__all__ = ["app"]
