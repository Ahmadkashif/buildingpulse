"""Domain types for the retrofit recomputation engine.

A :class:`Scenario` is the engine's per-intervention output: the static
library fields (id, name, description, reduction percentage, cost band,
citation) plus the recomputed Site EUI and the recomputed
:class:`~app.domain.ll97.types.Ll97Outlook` under that intervention.
"""

from __future__ import annotations

from dataclasses import dataclass

from app.domain.ll97.types import Ll97Outlook

__all__ = ["Scenario"]


@dataclass(frozen=True, slots=True)
class Scenario:
    """One recomputed retrofit scenario for a single building."""

    id: str
    name: str
    description: str
    reduction_pct: float
    cost_low_usd_per_sqft: float
    cost_high_usd_per_sqft: float
    citation: str
    recomputed_eui_kbtu_per_sqft: float
    outlook: Ll97Outlook
