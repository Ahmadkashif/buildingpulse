"""Unit tests for ScenarioResourceService.

The service is a thin façade over
:func:`app.domain.retrofits.engine.apply_scenarios`. These tests pin the
verb name and that errors from the engine surface unchanged.
"""

from __future__ import annotations

import pytest
from app.domain.ll97.types import (
    InvalidGrossFloorAreaError,
    UnknownPropertyTypeError,
)
from app.policy.retrofits import LIBRARY
from app.services.resource.scenario.service import ScenarioResourceService


def test_list_returns_one_scenario_per_library_entry() -> None:
    service = ScenarioResourceService()
    scenarios = service.list(
        property_type="office",
        baseline_eui_kbtu_per_sqft=200.0,
        gross_floor_area_sqft=50_000.0,
    )
    assert len(scenarios) == len(LIBRARY["office"])


def test_list_is_sorted_by_recomputed_total_fine_ascending() -> None:
    scenarios = ScenarioResourceService().list(
        property_type="office",
        baseline_eui_kbtu_per_sqft=200.0,
        gross_floor_area_sqft=50_000.0,
    )
    totals = [s.outlook.fine_current + s.outlook.fine_future for s in scenarios]
    assert totals == sorted(totals)


def test_unknown_property_type_raises() -> None:
    with pytest.raises(UnknownPropertyTypeError):
        ScenarioResourceService().list(
            property_type="warehouse",
            baseline_eui_kbtu_per_sqft=100.0,
            gross_floor_area_sqft=50_000.0,
        )


def test_invalid_sqft_raises() -> None:
    with pytest.raises(InvalidGrossFloorAreaError):
        ScenarioResourceService().list(
            property_type="office",
            baseline_eui_kbtu_per_sqft=100.0,
            gross_floor_area_sqft=0.0,
        )
