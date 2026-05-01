"""Peer-cohort domain package."""

from app.domain.peer.lookup import (
    AGE_BANDS,
    MIN_COHORT_SIZE,
    assign_age_band,
    lookup,
)
from app.domain.peer.types import PeerCohort, PeerOutlook

__all__ = [
    "AGE_BANDS",
    "MIN_COHORT_SIZE",
    "PeerCohort",
    "PeerOutlook",
    "assign_age_band",
    "lookup",
]
