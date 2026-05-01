"""Pure retrofit recomputation engine.

For each cited intervention in :data:`app.policy.retrofits.LIBRARY`, the
engine computes ``recomputed_eui = baseline_eui * (1 - reduction_pct)``
and runs :func:`app.domain.ll97.compute` to get the recomputed
:class:`~app.domain.ll97.types.Ll97Outlook`. The result is a tuple of
:class:`~app.domain.retrofits.types.Scenario`, sorted by recomputed
total fine ascending (lowest fine first), with intervention id as a
deterministic tiebreaker so the order is stable across calls.
"""

from __future__ import annotations

from datetime import date

from app.domain.ll97 import compute as compute_ll97
from app.domain.ll97.types import UnknownPropertyTypeError
from app.domain.retrofits.types import Scenario
from app.domain.types import PropertyType
from app.policy.retrofits import LIBRARY

__all__ = ["apply_scenarios"]


def apply_scenarios(
    property_type: PropertyType | str,
    baseline_eui: float,
    sqft: float,
    *,
    today: date | None = None,
) -> tuple[Scenario, ...]:
    """Recompute every library scenario for one building.

    Parameters
    ----------
    property_type:
        A :class:`PropertyType` enum member or its string slug. Must
        appear in :data:`app.policy.retrofits.LIBRARY`.
    baseline_eui:
        The building's baseline (predicted) Site EUI in kBTU per gross
        square foot per year.
    sqft:
        Gross floor area; passed through to the LL97 calculator and
        validated there.
    today:
        Anchor date for each scenario's ``fine_series``. Forwarded to
        :func:`app.domain.ll97.compute`. Defaults to ``date.today()``.

    Returns
    -------
    tuple[Scenario, ...]
        One :class:`Scenario` per library intervention for that property
        type, sorted by recomputed total fine ascending. Tied fines fall
        back on intervention ``id`` so ordering is fully deterministic.

    Raises
    ------
    UnknownPropertyTypeError
        If ``property_type`` is not in the retrofit library.
    InvalidGrossFloorAreaError
        If ``sqft`` is not strictly positive (raised by the LL97
        calculator).
    """
    key = str(property_type)
    entries = LIBRARY.get(key)  # type: ignore[arg-type]
    if entries is None:
        raise UnknownPropertyTypeError(f"no retrofit library entry for property_type {key!r}")

    scenarios: list[Scenario] = []
    for entry in entries:
        recomputed_eui = baseline_eui * (1.0 - entry.reduction_pct)
        outlook = compute_ll97(property_type, recomputed_eui, sqft, today=today)
        scenarios.append(
            Scenario(
                id=entry.id,
                name=entry.name,
                description=entry.description,
                reduction_pct=entry.reduction_pct,
                cost_low_usd_per_sqft=entry.cost_low_usd_per_sqft,
                cost_high_usd_per_sqft=entry.cost_high_usd_per_sqft,
                citation=entry.citation,
                recomputed_eui_kbtu_per_sqft=recomputed_eui,
                outlook=outlook,
            )
        )

    scenarios.sort(
        key=lambda s: (
            s.outlook.fine_current + s.outlook.fine_future,
            s.id,
        )
    )
    return tuple(scenarios)
