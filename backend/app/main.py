"""FastAPI application factory.

The app composes the v1 controllers under `/api`. CORS is locked to the
local frontend dev origin; production origins land in a later phase.
"""

from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1.predictions import router as predictions_router

app = FastAPI(title="BuildingPulse API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(predictions_router, prefix="/api")

__all__ = ["app"]
