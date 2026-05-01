"""Unit tests for the address-resolver dataclasses."""

from __future__ import annotations

import pytest
from app.domain.address.types import Ll84Index, Ll84Match, Ll84Miss, Ll84Record


def _record(**overrides: object) -> Ll84Record:
    base: dict[str, object] = {
        "bbl": "1000010001",
        "address_raw": "123 Main St",
        "address_normalized": "123 MAIN ST",
        "property_type": "office",
        "borough": "manhattan",
        "gross_floor_area_sqft": 50000,
        "year_built": 1980,
        "number_of_buildings": 1,
        "site_eui": 80.5,
    }
    base.update(overrides)
    return Ll84Record(**base)  # type: ignore[arg-type]


def test_record_constructs_with_named_fields() -> None:
    r = _record()

    assert r.bbl == "1000010001"
    assert r.property_type == "office"
    assert r.site_eui == 80.5


def test_record_allows_none_for_missing_eui() -> None:
    r = _record(site_eui=None)

    assert r.site_eui is None


def test_record_is_frozen() -> None:
    r = _record()

    with pytest.raises(Exception):
        r.bbl = "9999999999"  # type: ignore[misc]


def test_index_holds_records_as_tuple() -> None:
    idx = Ll84Index(records=(_record(),))

    assert isinstance(idx.records, tuple)
    assert len(idx.records) == 1


def test_match_carries_record_and_confidence() -> None:
    r = _record()
    m = Ll84Match(record=r, confidence="high")

    assert m.record is r
    assert m.confidence == "high"


def test_miss_carries_reason() -> None:
    miss = Ll84Miss(reason="not_found")

    assert miss.reason == "not_found"
