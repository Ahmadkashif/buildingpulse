"""Pure LL97 fine calculator.

Given a building's predicted Site EUI, gross floor area, and property
type, produce an :class:`Ll97Outlook` carrying the 2024-2029 and
2030-2034 cap values, the projected annual fine under each period, the
year-by-year fine timeline through 2034, and the headline ``at_risk``
verdict.

All cap values, the per-fuel emissions coefficient, and the per-tCO2e
fine rate are read from :mod:`app.policy.ll97_caps` — no statutory number
is hardcoded here.
"""

from __future__ import annotations

from datetime import date

from app.domain.ll97.types import (
    FineYear,
    InvalidGrossFloorAreaError,
    Ll97Outlook,
    UnknownPropertyTypeError,
)
from app.domain.types import PropertyType
from app.policy.ll97_caps import (
    CAPS,
    EMISSIONS_COEFFICIENT_TCO2E_PER_KBTU,
    FINE_USD_PER_TCO2E_OVER_CAP,
)

__all__ = ["FINAL_COMPLIANCE_YEAR", "FUTURE_PERIOD_START_YEAR", "compute"]


# Compliance-period boundaries from NYC Admin Code §28-320.3.1. Post-2034
# caps are not yet set by NYC, so the timeline ends at 2034.
FUTURE_PERIOD_START_YEAR: int = 2030
FINAL_COMPLIANCE_YEAR: int = 2034


def compute(
    property_type: PropertyType | str,
    predicted_eui_kbtu_per_sqft: float,
    gross_floor_area_sqft: float,
    *,
    today: date | None = None,
) -> Ll97Outlook:
    """Project a building's LL97 fine exposure.

    Parameters
    ----------
    property_type:
        A :class:`PropertyType` enum member or its string slug. Must
        appear in :data:`app.policy.ll97_caps.CAPS`.
    predicted_eui_kbtu_per_sqft:
        Predicted Site EUI in kBTU per gross square foot per year.
    gross_floor_area_sqft:
        Building gross floor area, strictly positive.
    today:
        Anchor date for the ``fine_series``. Defaults to ``date.today()``.

    Raises
    ------
    UnknownPropertyTypeError
        If ``property_type`` is not in the LL97 cap table.
    InvalidGrossFloorAreaError
        If ``gross_floor_area_sqft`` is not strictly positive.
    """
    if gross_floor_area_sqft <= 0:
        raise InvalidGrossFloorAreaError(
            f"gross_floor_area_sqft must be > 0, got {gross_floor_area_sqft!r}"
        )

    key = str(property_type)
    cap = CAPS.get(key)  # type: ignore[arg-type]
    if cap is None:
        raise UnknownPropertyTypeError(
            f"no LL97 cap configured for property_type {key!r}"
        )

    emissions_per_sqft = (
        predicted_eui_kbtu_per_sqft * EMISSIONS_COEFFICIENT_TCO2E_PER_KBTU
    )
    fine_current = _fine_for_period(
        emissions_per_sqft, cap.cap_2024_2029, gross_floor_area_sqft
    )
    fine_future = _fine_for_period(
        emissions_per_sqft, cap.cap_2030_2034, gross_floor_area_sqft
    )

    anchor = today if today is not None else date.today()
    fine_series = tuple(
        FineYear(
            year=year,
            projected_annual_fine_usd=(
                fine_future if year >= FUTURE_PERIOD_START_YEAR else fine_current
            ),
        )
        for year in range(anchor.year, FINAL_COMPLIANCE_YEAR + 1)
    )

    return Ll97Outlook(
        cap_current=cap.cap_2024_2029,
        cap_future=cap.cap_2030_2034,
        fine_current=fine_current,
        fine_future=fine_future,
        fine_series=fine_series,
        at_risk=fine_current > 0 or fine_future > 0,
    )


def _fine_for_period(
    emissions_per_sqft: float, cap_per_sqft: float, sqft: float
) -> float:
    """Annual USD fine for one compliance period (zero when under cap)."""
    excess_per_sqft = emissions_per_sqft - cap_per_sqft
    if excess_per_sqft <= 0:
        return 0.0
    return excess_per_sqft * sqft * FINE_USD_PER_TCO2E_OVER_CAP
