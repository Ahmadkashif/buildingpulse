"""FastAPI application factory.

The app composes the v1 controllers under `/api`. CORS is locked to the
local frontend dev origin; production origins land in a later phase.
On startup, the lifespan hook applies any pending SQL migrations.
"""

from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1.predictions import router as predictions_router
from app.repos.connection import connect
from app.repos.migrations import run_migrations


@asynccontextmanager
async def lifespan(_app: FastAPI) -> AsyncIterator[None]:
    conn = connect()
    try:
        run_migrations(conn)
    finally:
        conn.close()
    yield


app = FastAPI(title="BuildingPulse API", version="0.1.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(predictions_router, prefix="/api")

__all__ = ["app"]
