"""Unit tests for the peer-cohort dataclasses."""

from __future__ import annotations

import pytest
from app.domain.peer.types import PeerCohort, PeerOutlook


def test_peer_cohort_constructs_with_named_fields() -> None:
    c = PeerCohort(property_type="office", borough="manhattan", age_band="pre-1950")

    assert c.property_type == "office"
    assert c.borough == "manhattan"
    assert c.age_band == "pre-1950"


def test_peer_cohort_allows_none_for_broadened_keys() -> None:
    c = PeerCohort(property_type="office", borough=None, age_band=None)

    assert c.borough is None
    assert c.age_band is None


def test_peer_cohort_is_frozen() -> None:
    c = PeerCohort(property_type="office", borough="manhattan", age_band="pre-1950")

    with pytest.raises(Exception):
        c.borough = "bronx"  # type: ignore[misc]


def test_peer_outlook_constructs_with_named_fields() -> None:
    cohort = PeerCohort(property_type="office", borough="manhattan", age_band="pre-1950")
    o = PeerOutlook(
        cohort=cohort,
        cohort_size=100,
        median=70.0,
        p25=50.0,
        p75=90.0,
        percentile=68,
    )

    assert o.cohort is cohort
    assert o.cohort_size == 100
    assert o.median == 70.0
    assert o.p25 == 50.0
    assert o.p75 == 90.0
    assert o.percentile == 68


def test_peer_outlook_is_frozen() -> None:
    cohort = PeerCohort(property_type="office", borough="manhattan", age_band="pre-1950")
    o = PeerOutlook(cohort=cohort, cohort_size=1, median=1.0, p25=1.0, p75=1.0, percentile=50)

    with pytest.raises(Exception):
        o.percentile = 99  # type: ignore[misc]
