"""Unit tests for ``EuiPrediction`` dataclass."""

from __future__ import annotations

import pytest
from app.domain.prediction.types import EuiPrediction


def test_constructs_with_named_fields() -> None:
    p = EuiPrediction(value=87.3, low=65.2, high=109.4, model_version="baseline-lr-v1")

    assert p.value == 87.3
    assert p.low == 65.2
    assert p.high == 109.4
    assert p.model_version == "baseline-lr-v1"


def test_is_frozen() -> None:
    p = EuiPrediction(value=1.0, low=0.5, high=1.5, model_version="m1")

    with pytest.raises(Exception):  # FrozenInstanceError
        p.value = 2.0  # type: ignore[misc]
