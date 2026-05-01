"""Unit tests for ``app.domain.prediction.predictor``.

Targets: 100% branch coverage and ≥90% mutation kill rate. Every constant
the function uses (the 1.5 interval factor, the expm1 inverse transform,
each feature column name, each named argument) is pinned by an assertion
so a mutmut mutation has a test that fails.
"""

from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd
import pytest
from app.domain.prediction import EuiPrediction, predict_eui
from app.domain.prediction.predictor import FEATURE_COLUMNS, INTERVAL_K_RMSE


class _RecordingModel:
    """Captures the DataFrame the predictor passes in and returns ``log_value``."""

    def __init__(self, log_value: float) -> None:
        self._log_value = log_value
        self.calls: list[pd.DataFrame] = []

    def predict(self, x: Any) -> Any:
        self.calls.append(x)
        return np.array([self._log_value])


def _kwargs(**overrides: Any) -> dict[str, Any]:
    base: dict[str, Any] = {
        "property_type": "office",
        "borough": "manhattan",
        "gross_floor_area_sqft": 50_000,
        "year_built": 2000,
        "number_of_buildings": 1,
    }
    base.update(overrides)
    return base


def test_returns_eui_prediction_dataclass() -> None:
    model = _RecordingModel(log_value=float(np.log1p(100.0)))

    result = predict_eui(model=model, model_version="m1", rmse=10.0, **_kwargs())

    assert isinstance(result, EuiPrediction)


def test_value_is_expm1_of_model_output() -> None:
    # log1p(42) → expm1 round-trips back to exactly 42
    model = _RecordingModel(log_value=float(np.log1p(42.0)))

    result = predict_eui(model=model, model_version="m1", rmse=0.0, **_kwargs())

    assert result.value == pytest.approx(42.0)


def test_zero_log_prediction_inverts_to_zero() -> None:
    """expm1(0) == 0; rules out a swap to ``exp`` (which gives 1.0)."""
    model = _RecordingModel(log_value=0.0)

    result = predict_eui(model=model, model_version="m1", rmse=0.0, **_kwargs())

    assert result.value == pytest.approx(0.0)


def test_interval_half_width_is_1_5_times_rmse() -> None:
    model = _RecordingModel(log_value=float(np.log1p(100.0)))

    result = predict_eui(model=model, model_version="m1", rmse=10.0, **_kwargs())

    assert result.high - result.value == pytest.approx(15.0)
    assert result.value - result.low == pytest.approx(15.0)


def test_interval_factor_constant_is_1_5() -> None:
    assert INTERVAL_K_RMSE == 1.5


def test_low_is_value_minus_half_width() -> None:
    model = _RecordingModel(log_value=float(np.log1p(80.0)))

    result = predict_eui(model=model, model_version="m1", rmse=4.0, **_kwargs())

    assert result.low == pytest.approx(80.0 - 6.0)


def test_high_is_value_plus_half_width() -> None:
    model = _RecordingModel(log_value=float(np.log1p(80.0)))

    result = predict_eui(model=model, model_version="m1", rmse=4.0, **_kwargs())

    assert result.high == pytest.approx(80.0 + 6.0)


def test_zero_rmse_collapses_interval_onto_value() -> None:
    model = _RecordingModel(log_value=float(np.log1p(50.0)))

    result = predict_eui(model=model, model_version="m1", rmse=0.0, **_kwargs())

    assert result.low == pytest.approx(50.0)
    assert result.high == pytest.approx(50.0)


def test_model_version_is_passed_through_unchanged() -> None:
    model = _RecordingModel(log_value=0.0)

    result = predict_eui(model=model, model_version="baseline-lr-v1", rmse=1.0, **_kwargs())

    assert result.model_version == "baseline-lr-v1"


def test_value_changes_when_model_output_changes() -> None:
    a = predict_eui(
        model=_RecordingModel(log_value=float(np.log1p(10.0))),
        model_version="m1",
        rmse=0.0,
        **_kwargs(),
    )
    b = predict_eui(
        model=_RecordingModel(log_value=float(np.log1p(20.0))),
        model_version="m1",
        rmse=0.0,
        **_kwargs(),
    )

    assert a.value != b.value
    assert a.value == pytest.approx(10.0)
    assert b.value == pytest.approx(20.0)


def test_feature_columns_pin_exact_names_and_order() -> None:
    assert FEATURE_COLUMNS == (
        "property_type",
        "borough",
        "gross_floor_area_sqft",
        "year_built",
        "number_of_buildings",
    )


def test_features_passed_to_model_have_canonical_columns_and_values() -> None:
    model = _RecordingModel(log_value=0.0)

    predict_eui(
        model=model,
        model_version="m1",
        rmse=1.0,
        property_type="hotel",
        borough="bronx",
        gross_floor_area_sqft=12_345,
        year_built=1899,
        number_of_buildings=3,
    )

    assert len(model.calls) == 1
    df = model.calls[0]
    assert list(df.columns) == list(FEATURE_COLUMNS)
    assert df.shape == (1, 5)
    row = df.iloc[0]
    assert row["property_type"] == "hotel"
    assert row["borough"] == "bronx"
    assert int(row["gross_floor_area_sqft"]) == 12_345
    assert int(row["year_built"]) == 1899
    assert int(row["number_of_buildings"]) == 3


def test_handles_2d_model_output_array() -> None:
    """Some sklearn estimators return shape ``(n, 1)``; ``reshape(-1)`` flattens."""

    class TwoDModel:
        def predict(self, _x: Any) -> Any:
            return np.array([[float(np.log1p(7.0))]])

    result = predict_eui(model=TwoDModel(), model_version="m1", rmse=0.0, **_kwargs())

    assert result.value == pytest.approx(7.0)


def test_takes_first_row_when_model_returns_multiple_predictions() -> None:
    """The predictor builds a single-row frame, so only ``[0]`` is meaningful."""

    class MultiModel:
        def predict(self, _x: Any) -> Any:
            return np.array([float(np.log1p(11.0)), float(np.log1p(99.0))])

    result = predict_eui(model=MultiModel(), model_version="m1", rmse=0.0, **_kwargs())

    assert result.value == pytest.approx(11.0)


def test_rmse_is_coerced_to_float() -> None:
    """``rmse`` may arrive as numpy scalar / int; multiplication must still work."""
    model = _RecordingModel(log_value=float(np.log1p(20.0)))

    result = predict_eui(model=model, model_version="m1", rmse=2, **_kwargs())

    assert result.high == pytest.approx(23.0)
    assert result.low == pytest.approx(17.0)
