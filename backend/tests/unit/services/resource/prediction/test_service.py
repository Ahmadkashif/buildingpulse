"""Unit tests for ``PredictionResourceService``.

The service is a thin pass-through; tests confirm it pulls model, version,
and rmse from the registry and forwards each feature primitive to
``predict_eui``.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import joblib
import numpy as np
import pytest
from app.domain.prediction.types import EuiPrediction
from app.repos.artifact_registry import ArtifactRegistry
from app.services.resource.prediction.service import PredictionResourceService


class _FixedModel:
    def __init__(self, log_value: float) -> None:
        self._log_value = log_value
        self.call_args: list[Any] = []

    def predict(self, x: Any) -> Any:
        self.call_args.append(x)
        return np.array([self._log_value])


@pytest.fixture(autouse=True)
def _reset_counter() -> None:
    ArtifactRegistry._reset_load_count()


def _build_registry(tmp_path: Path, *, model: Any, model_version: str, rmse: float) -> ArtifactRegistry:
    joblib.dump(model, tmp_path / "model.pkl")
    (tmp_path / "metrics.json").write_text(
        json.dumps(
            {
                "modelVersion": model_version,
                "rmse": rmse,
                "r2": 0.9,
                "trainRows": 1,
                "testRows": 1,
                "trainedAt": "2026-05-01T00:00:00Z",
            }
        )
    )
    return ArtifactRegistry(tmp_path)


def test_predict_returns_eui_prediction(tmp_path: Path) -> None:
    model = _FixedModel(log_value=float(np.log1p(80.0)))
    registry = _build_registry(tmp_path, model=model, model_version="srv-v1", rmse=4.0)
    service = PredictionResourceService(registry)

    result = service.predict(
        property_type="office",
        borough="manhattan",
        gross_floor_area_sqft=50_000,
        year_built=2000,
        number_of_buildings=1,
    )

    assert isinstance(result, EuiPrediction)
    assert result.value == pytest.approx(80.0)
    assert result.high == pytest.approx(80.0 + 1.5 * 4.0)
    assert result.low == pytest.approx(80.0 - 1.5 * 4.0)
    assert result.model_version == "srv-v1"


def test_predict_forwards_feature_primitives(tmp_path: Path) -> None:
    model = _FixedModel(log_value=0.0)
    registry = _build_registry(tmp_path, model=model, model_version="srv-v1", rmse=1.0)
    service = PredictionResourceService(registry)

    service.predict(
        property_type="hotel",
        borough="bronx",
        gross_floor_area_sqft=12_345,
        year_built=1899,
        number_of_buildings=3,
    )

    # joblib roundtrips a copy; pull the actual model the service used.
    used_model = registry.predictor
    df = used_model.call_args[0]
    assert df.iloc[0]["property_type"] == "hotel"
    assert df.iloc[0]["borough"] == "bronx"
    assert int(df.iloc[0]["gross_floor_area_sqft"]) == 12_345
    assert int(df.iloc[0]["year_built"]) == 1899
    assert int(df.iloc[0]["number_of_buildings"]) == 3
