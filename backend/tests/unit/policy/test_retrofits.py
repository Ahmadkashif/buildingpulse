"""Statement-coverage tests for ``app.policy.retrofits``."""

from __future__ import annotations

from dataclasses import FrozenInstanceError
from typing import get_args

import pytest
from app.policy import retrofits
from app.policy.ll97_caps import PropertyType
from app.policy.retrofits import LIBRARY, RetrofitScenario
from pydantic import ValidationError

REQUIRED_TYPES = set(get_args(PropertyType))


def _make_scenario(**overrides: object) -> RetrofitScenario:
    base: dict[str, object] = {
        "id": "test-id",
        "name": "Test scenario",
        "description": "A test retrofit scenario.",
        "reduction_pct": 0.2,
        "cost_low_usd_per_sqft": 5.0,
        "cost_high_usd_per_sqft": 15.0,
        "citation": "Test citation",
    }
    base.update(overrides)
    return RetrofitScenario(**base)  # type: ignore[arg-type]


def test_library_covers_every_property_type() -> None:
    assert set(LIBRARY.keys()) == REQUIRED_TYPES


def test_library_has_three_to_five_interventions_per_type() -> None:
    for property_type, scenarios in LIBRARY.items():
        assert 3 <= len(scenarios) <= 5, property_type


def test_every_scenario_has_a_citation() -> None:
    for scenarios in LIBRARY.values():
        for scenario in scenarios:
            assert scenario.citation
            assert len(scenario.citation) > 5


def test_scenario_ids_unique_within_property_type() -> None:
    for property_type, scenarios in LIBRARY.items():
        ids = [s.id for s in scenarios]
        assert len(ids) == len(set(ids)), property_type


def test_reduction_pcts_are_within_zero_one() -> None:
    for scenarios in LIBRARY.values():
        for scenario in scenarios:
            assert 0.0 < scenario.reduction_pct <= 1.0


def test_cost_bands_are_nonnegative_and_ordered() -> None:
    for scenarios in LIBRARY.values():
        for scenario in scenarios:
            assert scenario.cost_low_usd_per_sqft >= 0.0
            assert scenario.cost_high_usd_per_sqft >= scenario.cost_low_usd_per_sqft


def test_scenario_is_frozen() -> None:
    scenario = LIBRARY["office"][0]
    with pytest.raises(FrozenInstanceError):
        scenario.reduction_pct = 0.5  # type: ignore[misc]


def test_rejects_reduction_pct_above_one() -> None:
    with pytest.raises(ValidationError):
        _make_scenario(reduction_pct=1.5)


def test_rejects_reduction_pct_zero() -> None:
    with pytest.raises(ValidationError):
        _make_scenario(reduction_pct=0.0)


def test_rejects_negative_reduction_pct() -> None:
    with pytest.raises(ValidationError):
        _make_scenario(reduction_pct=-0.1)


def test_rejects_negative_low_cost() -> None:
    with pytest.raises(ValidationError):
        _make_scenario(cost_low_usd_per_sqft=-1.0)


def test_rejects_negative_high_cost() -> None:
    with pytest.raises(ValidationError):
        _make_scenario(cost_high_usd_per_sqft=-1.0, cost_low_usd_per_sqft=0.0)


def test_rejects_inverted_cost_band() -> None:
    with pytest.raises(ValidationError):
        _make_scenario(cost_low_usd_per_sqft=20.0, cost_high_usd_per_sqft=10.0)


def test_rejects_empty_citation() -> None:
    with pytest.raises(ValidationError):
        _make_scenario(citation="")


def test_rejects_empty_id() -> None:
    with pytest.raises(ValidationError):
        _make_scenario(id="")


def test_rejects_empty_name() -> None:
    with pytest.raises(ValidationError):
        _make_scenario(name="")


def test_rejects_empty_description() -> None:
    with pytest.raises(ValidationError):
        _make_scenario(description="")


def test_build_library_raises_on_missing_property_type(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    truncated = {k: v for k, v in retrofits._ENTRIES.items() if k != "office"}
    monkeypatch.setattr(retrofits, "_ENTRIES", truncated)

    with pytest.raises(ValueError, match="missing required property types"):
        retrofits._build_library()


def test_build_library_raises_on_unknown_property_type(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    extra = dict(retrofits._ENTRIES)
    extra["bogus-type"] = retrofits._ENTRIES["office"]  # type: ignore[index]
    monkeypatch.setattr(retrofits, "_ENTRIES", extra)

    with pytest.raises(ValueError, match="unknown property types"):
        retrofits._build_library()


def test_build_library_raises_when_count_out_of_range(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    too_few = dict(retrofits._ENTRIES)
    too_few["office"] = retrofits._ENTRIES["office"][:2]
    monkeypatch.setattr(retrofits, "_ENTRIES", too_few)

    with pytest.raises(ValueError, match="3.5"):
        retrofits._build_library()


def test_build_library_raises_on_duplicate_scenario_id(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    office = retrofits._ENTRIES["office"]
    duplicated = dict(retrofits._ENTRIES)
    duplicated["office"] = (*office, office[0])
    monkeypatch.setattr(retrofits, "_ENTRIES", duplicated)

    with pytest.raises(ValueError, match="duplicate retrofit id"):
        retrofits._build_library()
