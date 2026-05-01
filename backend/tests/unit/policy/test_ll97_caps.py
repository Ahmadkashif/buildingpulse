"""Statement-coverage tests for ``app.policy.ll97_caps``."""

from __future__ import annotations

from dataclasses import FrozenInstanceError
from typing import get_args

import pytest
from app.policy import ll97_caps
from app.policy.ll97_caps import CAPS, EmissionsCap, PropertyType
from pydantic import ValidationError

REQUIRED_TYPES = set(get_args(PropertyType))


def test_caps_contains_all_six_property_types() -> None:
    assert set(CAPS.keys()) == REQUIRED_TYPES
    assert len(CAPS) == 6


def test_each_entry_has_a_citation() -> None:
    for entry in CAPS.values():
        assert entry.citation
        assert "LL97" in entry.citation or "Occupancy" in entry.citation


def test_caps_ratchet_down_in_2030() -> None:
    for entry in CAPS.values():
        assert entry.cap_2030_2034 <= entry.cap_2024_2029
        assert entry.cap_2024_2029 > 0
        assert entry.cap_2030_2034 > 0


def test_emissions_cap_is_frozen() -> None:
    cap = CAPS["office"]
    with pytest.raises(FrozenInstanceError):
        cap.cap_2024_2029 = 0.5  # type: ignore[misc]


def test_emissions_cap_rejects_nonpositive_caps() -> None:
    with pytest.raises(ValidationError):
        EmissionsCap(
            property_type="office",
            cap_2024_2029=0.0,
            cap_2030_2034=0.001,
            citation="x",
        )
    with pytest.raises(ValidationError):
        EmissionsCap(
            property_type="office",
            cap_2024_2029=0.001,
            cap_2030_2034=-0.5,
            citation="x",
        )


def test_emissions_cap_rejects_empty_citation() -> None:
    with pytest.raises(ValidationError):
        EmissionsCap(
            property_type="office",
            cap_2024_2029=0.001,
            cap_2030_2034=0.0005,
            citation="",
        )


def test_build_caps_raises_on_missing_property_type(monkeypatch: pytest.MonkeyPatch) -> None:
    truncated = ll97_caps._ENTRIES[:-1]
    monkeypatch.setattr(ll97_caps, "_ENTRIES", truncated)

    with pytest.raises(ValueError, match="missing required property types"):
        ll97_caps._build_caps()


def test_build_caps_raises_on_duplicate_property_type(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    duplicated = (*ll97_caps._ENTRIES, ll97_caps._ENTRIES[0])
    monkeypatch.setattr(ll97_caps, "_ENTRIES", duplicated)

    with pytest.raises(ValueError, match="duplicate LL97 cap entry"):
        ll97_caps._build_caps()


def test_build_caps_raises_when_2030_cap_loosens(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    bad = EmissionsCap(
        property_type="office",
        cap_2024_2029=0.001,
        cap_2030_2034=0.002,  # looser than current — must fail
        citation="bogus",
    )
    swapped = tuple(
        bad if e.property_type == "office" else e for e in ll97_caps._ENTRIES
    )
    monkeypatch.setattr(ll97_caps, "_ENTRIES", swapped)

    with pytest.raises(ValueError, match="ratchet down"):
        ll97_caps._build_caps()
