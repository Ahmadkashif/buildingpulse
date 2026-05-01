"""Domain types for the peer-cohort lookup role."""

from __future__ import annotations

from dataclasses import dataclass

__all__ = ["PeerCohort", "PeerOutlook"]


@dataclass(frozen=True, slots=True)
class PeerCohort:
    """The cohort actually used to score a building.

    ``borough`` is ``None`` when the lookup fell back from a borough-specific
    cohort to a city-wide cohort. ``age_band`` is ``None`` when the lookup
    fell back further to all ages.
    """

    property_type: str
    borough: str | None
    age_band: str | None


@dataclass(frozen=True, slots=True)
class PeerOutlook:
    """Where a predicted EUI sits inside its peer cohort.

    All EUI fields are kBTU/ft²/year. ``percentile`` is an integer in
    ``[0, 100]`` — percentile rank of the predicted EUI inside the cohort
    that was actually used.
    """

    cohort: PeerCohort
    cohort_size: int
    median: float
    p25: float
    p75: float
    percentile: int
