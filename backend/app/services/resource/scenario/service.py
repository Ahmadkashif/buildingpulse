"""Scenario resource service.

Composes :func:`app.domain.retrofits.engine.apply_scenarios` for one
building's baseline. The service holds no I/O and no repos — the retrofit
library is a frozen policy module imported directly by the engine — so
this is a thin façade that fixes the verb (``list``) on the scenario
resource and keeps the controller import-linter compliant.
"""

from __future__ import annotations

from app.domain.retrofits.engine import apply_scenarios
from app.domain.retrofits.types import Scenario

__all__ = ["ScenarioResourceService"]


class ScenarioResourceService:
    """Owns the `list` verb on the scenario resource."""

    def list(
        self,
        *,
        property_type: str,
        baseline_eui_kbtu_per_sqft: float,
        gross_floor_area_sqft: float,
    ) -> tuple[Scenario, ...]:
        """Recompute every library scenario for the given baseline.

        Returns scenarios in the engine's deterministic order (lowest
        recomputed total fine first, intervention id as tiebreaker).
        Raises :class:`~app.domain.ll97.types.UnknownPropertyTypeError`
        if ``property_type`` is not in the retrofit library, and
        :class:`~app.domain.ll97.types.InvalidGrossFloorAreaError` if
        ``gross_floor_area_sqft`` is not strictly positive.
        """
        return apply_scenarios(
            property_type=property_type,
            baseline_eui=baseline_eui_kbtu_per_sqft,
            sqft=gross_floor_area_sqft,
        )
