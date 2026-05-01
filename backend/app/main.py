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

from app.api.v1.leads import router as leads_router
from app.api.v1.predictions import router as predictions_router
from app.api.v1.sponsor import router as sponsor_router
from app.deps import (
    RequestIdMiddleware,
    configure_logging,
    configure_telemetry,
    get_logger,
    init_app_config,
    init_artifact_registry,
    init_peer_cohorts_registry,
    instrument_app,
)
from app.repos.connection import connect
from app.repos.migrations import run_migrations

configure_logging()
configure_telemetry()


@asynccontextmanager
async def lifespan(_app: FastAPI) -> AsyncIterator[None]:
    log = get_logger("app.main")
    config = init_app_config()
    log.info("startup.config_loaded", sponsor_id=config.sponsor.id)
    conn = connect()
    try:
        run_migrations(conn)
        log.info("startup.migrations_applied")
    finally:
        conn.close()
    registry = init_artifact_registry()
    log.info("startup.artifacts_loaded", model_version=registry.model_version)
    cohorts = init_peer_cohorts_registry()
    log.info("startup.peer_cohorts_loaded", rows=int(cohorts.cohorts.shape[0]))
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
app.include_router(sponsor_router, prefix="/api")
app.include_router(leads_router, prefix="/api")

__all__ = ["app"]
