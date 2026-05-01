"""Unit tests for ``app.domain.ll97.calculator``.

Targets: 100% branch coverage and ≥90% mutation kill rate. Caps and the
fine rate are read from the production ``app.policy.ll97_caps`` module —
no fixture redefinitions — so a config drift breaks these tests on
purpose.
"""

from __future__ import annotations

from datetime import date

import pytest
from app.domain.ll97 import (
    FINAL_COMPLIANCE_YEAR,
    FUTURE_PERIOD_START_YEAR,
    InvalidGrossFloorAreaError,
    UnknownPropertyTypeError,
    compute,
)
from app.domain.types import PropertyType
from app.policy.ll97_caps import (
    CAPS,
    EMISSIONS_COEFFICIENT_TCO2E_PER_KBTU,
    FINE_USD_PER_TCO2E_OVER_CAP,
)


def _expected_fine(eui: float, cap_per_sqft: float, sqft: float) -> float:
    excess = eui * EMISSIONS_COEFFICIENT_TCO2E_PER_KBTU - cap_per_sqft
    if excess <= 0:
        return 0.0
    return excess * sqft * FINE_USD_PER_TCO2E_OVER_CAP


def test_under_cap_building_has_no_fine_and_flat_zero_series() -> None:
    # An efficient office well under both caps: verdict false, every
    # series row is zero.
    eui = 20.0
    sqft = 30_000.0
    today = date(2026, 1, 1)

    outlook = compute(PropertyType.OFFICE, eui, sqft, today=today)

    cap = CAPS["office"]
    assert outlook.cap_current == cap.cap_2024_2029
    assert outlook.cap_future == cap.cap_2030_2034
    assert outlook.fine_current == 0.0
    assert outlook.fine_future == 0.0
    assert outlook.at_risk is False
    assert all(row.projected_annual_fine_usd == 0.0 for row in outlook.fine_series)


def test_over_both_caps_building_has_positive_fines_and_monotone_series() -> None:
    # A high-EUI hospital is over both caps; the 2030 fine must be
    # strictly larger than the 2024 fine because the cap ratchets down.
    eui = 500.0
    sqft = 80_000.0
    today = date(2026, 1, 1)

    outlook = compute(PropertyType.HOSPITAL, eui, sqft, today=today)

    expected_current = _expected_fine(eui, CAPS["hospital"].cap_2024_2029, sqft)
    expected_future = _expected_fine(eui, CAPS["hospital"].cap_2030_2034, sqft)
    assert outlook.fine_current == pytest.approx(expected_current)
    assert outlook.fine_future == pytest.approx(expected_future)
    assert outlook.fine_current > 0.0
    assert outlook.fine_future > outlook.fine_current
    assert outlook.at_risk is True


def test_straddles_2030_office_is_clean_now_and_fined_after_the_cliff() -> None:
    # An office at 100 kBTU/sqft sits under the 2024-2029 cap but over
    # the tighter 2030-2034 cap — the textbook "cliff at 2030" case.
    eui = 100.0
    sqft = 50_000.0
    today = date(2024, 1, 1)

    outlook = compute(PropertyType.OFFICE, eui, sqft, today=today)

    assert outlook.fine_current == 0.0
    assert outlook.fine_future > 0.0
    assert outlook.at_risk is True
    pre_cliff = [
        row for row in outlook.fine_series if row.year < FUTURE_PERIOD_START_YEAR
    ]
    post_cliff = [
        row for row in outlook.fine_series if row.year >= FUTURE_PERIOD_START_YEAR
    ]
    assert pre_cliff and post_cliff
    assert all(row.projected_annual_fine_usd == 0.0 for row in pre_cliff)
    assert all(
        row.projected_annual_fine_usd == outlook.fine_future for row in post_cliff
    )


def test_fine_series_spans_today_year_through_2034_in_order() -> None:
    today = date(2027, 6, 15)

    outlook = compute(PropertyType.RETAIL, 50.0, 25_000.0, today=today)

    years = [row.year for row in outlook.fine_series]
    assert years == list(range(today.year, FINAL_COMPLIANCE_YEAR + 1))
    assert years == sorted(years)
    assert years[0] == today.year
    assert years[-1] == FINAL_COMPLIANCE_YEAR


def test_unknown_property_type_raises_typed_error() -> None:
    with pytest.raises(UnknownPropertyTypeError, match="warehouse"):
        compute("warehouse", 100.0, 50_000.0, today=date(2026, 1, 1))


def test_non_positive_gross_floor_area_raises_typed_error() -> None:
    with pytest.raises(InvalidGrossFloorAreaError, match="gross_floor_area_sqft"):
        compute(PropertyType.OFFICE, 100.0, 0.0, today=date(2026, 1, 1))
    with pytest.raises(InvalidGrossFloorAreaError, match="-1"):
        compute(PropertyType.OFFICE, 100.0, -1.0, today=date(2026, 1, 1))
