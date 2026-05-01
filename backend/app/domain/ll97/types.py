"""Domain types for the LL97 fine calculator role.

The shapes mirror what the report renders and what the API serializes —
``Ll97Outlook`` carries the period caps, the period fines, the per-year
``fine_series`` for the timeline chart, and the ``at_risk`` boolean used
for the verdict pill.
"""

from __future__ import annotations

from dataclasses import dataclass

__all__ = [
    "FineYear",
    "InvalidGrossFloorAreaError",
    "Ll97Error",
    "Ll97Outlook",
    "UnknownPropertyTypeError",
]


@dataclass(frozen=True, slots=True)
class FineYear:
    """One row of the projected-fine timeline."""

    year: int
    projected_annual_fine_usd: float


@dataclass(frozen=True, slots=True)
class Ll97Outlook:
    """LL97 exposure for a single building.

    ``cap_*`` are tCO2e per gross square foot per year. ``fine_*`` are
    annual USD totals for the whole building under that period's cap.
    ``fine_series`` is one row per year from the year of ``today`` through
    2034 inclusive — flat within each compliance period, with a step at
    2030 ("the cliff").
    """

    cap_current: float
    cap_future: float
    fine_current: float
    fine_future: float
    fine_series: tuple[FineYear, ...]
    at_risk: bool


class Ll97Error(Exception):
    """Base class for LL97 calculator errors."""


class UnknownPropertyTypeError(Ll97Error):
    """Raised when ``property_type`` is not in the LL97 cap table."""


class InvalidGrossFloorAreaError(Ll97Error):
    """Raised when ``gross_floor_area_sqft`` is not strictly positive."""
