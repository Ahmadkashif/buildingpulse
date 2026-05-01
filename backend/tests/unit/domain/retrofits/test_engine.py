"""Unit tests for ``app.domain.retrofits.engine``.

Targets: 100% branch coverage and ≥90% mutation kill rate. Library data
is read live from ``app.policy.retrofits.LIBRARY`` — config drift breaks
these tests by design.
"""

from __future__ import annotations

from datetime import date

import pytest
from app.domain.ll97 import UnknownPropertyTypeError
from app.domain.ll97 import compute as compute_ll97
from app.domain.ll97.types import InvalidGrossFloorAreaError
from app.domain.retrofits import Scenario, apply_scenarios
from app.domain.types import PropertyType
from app.policy.retrofits import LIBRARY
from hypothesis import given, settings
from hypothesis import strategies as st


def _baseline_total_fine(
    property_type: PropertyType, eui: float, sqft: float, today: date
) -> float:
    outlook = compute_ll97(property_type, eui, sqft, today=today)
    return outlook.fine_current + outlook.fine_future


def test_returns_one_scenario_per_library_entry_for_each_property_type() -> None:
    today = date(2026, 1, 1)
    for prop in PropertyType:
        result = apply_scenarios(prop, 200.0, 30_000.0, today=today)
        assert len(result) == len(LIBRARY[prop.value])
        assert {s.id for s in result} == {e.id for e in LIBRARY[prop.value]}
        for scenario in result:
            assert isinstance(scenario, Scenario)


def test_recomputed_eui_applies_reduction_pct() -> None:
    today = date(2026, 1, 1)
    baseline = 250.0
    result = apply_scenarios(PropertyType.OFFICE, baseline, 50_000.0, today=today)
    by_id = {s.id: s for s in result}
    for entry in LIBRARY["office"]:
        s = by_id[entry.id]
        assert s.recomputed_eui_kbtu_per_sqft == pytest.approx(
            baseline * (1.0 - entry.reduction_pct)
        )
        # Static fields are forwarded verbatim.
        assert s.name == entry.name
        assert s.description == entry.description
        assert s.reduction_pct == entry.reduction_pct
        assert s.cost_low_usd_per_sqft == entry.cost_low_usd_per_sqft
        assert s.cost_high_usd_per_sqft == entry.cost_high_usd_per_sqft
        assert s.citation == entry.citation


def test_outlook_matches_direct_calculator_call() -> None:
    today = date(2026, 6, 1)
    baseline = 220.0
    sqft = 40_000.0
    result = apply_scenarios(PropertyType.HOTEL, baseline, sqft, today=today)
    by_id = {s.id: s for s in result}
    for entry in LIBRARY["hotel"]:
        expected = compute_ll97(
            PropertyType.HOTEL,
            baseline * (1.0 - entry.reduction_pct),
            sqft,
            today=today,
        )
        assert by_id[entry.id].outlook == expected


def test_results_sorted_by_recomputed_total_fine_ascending() -> None:
    today = date(2026, 1, 1)
    # Heavily over-cap input so multiple scenarios still leave a fine.
    result = apply_scenarios(PropertyType.OFFICE, 400.0, 100_000.0, today=today)
    totals = [s.outlook.fine_current + s.outlook.fine_future for s in result]
    assert totals == sorted(totals)


def test_ordering_is_stable_across_calls() -> None:
    today = date(2026, 1, 1)
    a = apply_scenarios(PropertyType.MIXED_USE, 350.0, 60_000.0, today=today)
    b = apply_scenarios(PropertyType.MIXED_USE, 350.0, 60_000.0, today=today)
    assert [s.id for s in a] == [s.id for s in b]
    assert a == b


def test_tiebreaker_is_scenario_id_when_fines_equal() -> None:
    # An under-cap building zeroes every recomputed fine, so the total
    # is tied at 0 across all scenarios. The id-tiebreaker must produce
    # alphabetical ordering.
    today = date(2026, 1, 1)
    result = apply_scenarios(PropertyType.OFFICE, 10.0, 30_000.0, today=today)
    ids = [s.id for s in result]
    assert ids == sorted(ids)
    for s in result:
        assert s.outlook.fine_current == 0.0
        assert s.outlook.fine_future == 0.0


def test_unknown_property_type_raises() -> None:
    with pytest.raises(UnknownPropertyTypeError, match="warehouse"):
        apply_scenarios("warehouse", 100.0, 30_000.0, today=date(2026, 1, 1))


def test_invalid_sqft_propagates_calculator_error() -> None:
    with pytest.raises(InvalidGrossFloorAreaError):
        apply_scenarios(PropertyType.OFFICE, 100.0, 0.0, today=date(2026, 1, 1))


def test_string_property_type_accepted() -> None:
    today = date(2026, 1, 1)
    via_enum = apply_scenarios(PropertyType.RETAIL, 200.0, 25_000.0, today=today)
    via_str = apply_scenarios("retail", 200.0, 25_000.0, today=today)
    assert via_enum == via_str


def test_today_threaded_into_each_scenario_outlook() -> None:
    # Two different anchor dates must produce two different fine_series
    # first-year values; this pins the engine's `today` argument as
    # actually forwarded to compute() rather than dropped or replaced.
    early = date(2026, 1, 1)
    late = date(2029, 6, 1)
    early_result = apply_scenarios(PropertyType.OFFICE, 200.0, 30_000.0, today=early)
    late_result = apply_scenarios(PropertyType.OFFICE, 200.0, 30_000.0, today=late)
    for s_early, s_late in zip(early_result, late_result, strict=True):
        assert s_early.outlook.fine_series[0].year == early.year
        assert s_late.outlook.fine_series[0].year == late.year


def test_today_default_uses_date_today(monkeypatch: pytest.MonkeyPatch) -> None:
    # Forwarding `today=None` defers to the calculator's default. Pinning
    # date.today() in the calculator module gives us a deterministic check
    # that the engine threads today through (vs. silently injecting a
    # different anchor).
    fixed = date(2027, 3, 15)

    class _FixedDate(date):
        @classmethod
        def today(cls) -> date:
            return fixed

    monkeypatch.setattr("app.domain.ll97.calculator.date", _FixedDate)

    result = apply_scenarios(PropertyType.OFFICE, 200.0, 30_000.0)
    for s in result:
        assert s.outlook.fine_series[0].year == fixed.year


@given(
    eui=st.floats(min_value=300.0, max_value=2000.0, allow_nan=False),
    sqft=st.floats(min_value=25_000.0, max_value=2_000_000.0, allow_nan=False),
    prop=st.sampled_from(list(PropertyType)),
)
@settings(max_examples=80, deadline=None)
def test_property_recomputed_fine_never_exceeds_baseline(
    eui: float, sqft: float, prop: PropertyType
) -> None:
    today = date(2026, 1, 1)
    baseline_outlook = compute_ll97(prop, eui, sqft, today=today)
    baseline_total = baseline_outlook.fine_current + baseline_outlook.fine_future
    scenarios = apply_scenarios(prop, eui, sqft, today=today)
    for s in scenarios:
        assert s.outlook.fine_current <= baseline_outlook.fine_current
        assert s.outlook.fine_future <= baseline_outlook.fine_future
        assert s.outlook.fine_current + s.outlook.fine_future <= baseline_total
