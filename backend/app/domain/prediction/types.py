"""Domain types for the EUI prediction role."""

from __future__ import annotations

from dataclasses import dataclass

__all__ = ["EuiPrediction"]


@dataclass(frozen=True, slots=True)
class EuiPrediction:
    """A single Site EUI point estimate with a symmetric prediction interval.

    All three numeric fields are kBTU/ft²/year. ``model_version`` mirrors
    ``metrics.json`` so callers can attribute a prediction to the artifact
    that produced it.
    """

    value: float
    low: float
    high: float
    model_version: str
