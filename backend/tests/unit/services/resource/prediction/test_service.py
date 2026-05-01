"""Unit tests for ``PredictionResourceService``.

The service composes the EUI predictor with the peer-cohort lookup; tests
confirm it pulls model, version, and rmse from the registry, forwards each
feature primitive to ``predict_eui``, and scores the predicted EUI against
the cohorts frame.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import joblib
import numpy as np
import pandas as pd
import pytest
from app.domain.peer.types import PeerOutlook
from app.domain.prediction.types import EuiPrediction
from app.repos.artifact_registry import ArtifactRegistry
from app.repos.peer_cohorts_registry import PeerCohortsRegistry
from app.services.resource.prediction.service import (
    PredictionResourceService,
    PredictionResult,
)


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


def _write_peer_cohorts(directory: Path) -> None:
    rows: list[dict[str, object]] = []
    for prop in ("office", "hotel"):
        for borough in ("manhattan", "bronx"):
            for age in ("pre-1950", "1950-1979", "1980-1999", "2000-plus"):
                eui = [float(i) for i in range(1, 51)]
                rows.append(
                    {
                        "property_type": prop,
                        "borough": borough,
                        "age_band": age,
                        "cohort_size": len(eui),
                        "p25": float(np.percentile(eui, 25)),
                        "median": float(np.percentile(eui, 50)),
                        "p75": float(np.percentile(eui, 75)),
                        "eui_sorted": eui,
                    }
                )
    pd.DataFrame(rows).to_parquet(
        directory / "peer_cohorts.parquet", engine="pyarrow", compression="snappy",
        index=False,
    )


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


def _build_peer_registry(tmp_path: Path) -> PeerCohortsRegistry:
    _write_peer_cohorts(tmp_path)
    return PeerCohortsRegistry(tmp_path)


def test_predict_returns_eui_prediction(tmp_path: Path) -> None:
    model = _FixedModel(log_value=float(np.log1p(80.0)))
    registry = _build_registry(tmp_path, model=model, model_version="srv-v1", rmse=4.0)
    peers = _build_peer_registry(tmp_path)
    service = PredictionResourceService(registry, peers)

    result = service.predict(
        property_type="office",
        borough="manhattan",
        gross_floor_area_sqft=50_000,
        year_built=2000,
        number_of_buildings=1,
    )

    assert isinstance(result, PredictionResult)
    assert isinstance(result.eui, EuiPrediction)
    assert isinstance(result.peer, PeerOutlook)
    assert result.eui.value == pytest.approx(80.0)
    assert result.eui.high == pytest.approx(80.0 + 1.5 * 4.0)
    assert result.eui.low == pytest.approx(80.0 - 1.5 * 4.0)
    assert result.eui.model_version == "srv-v1"
    assert 0 <= result.peer.percentile <= 100
    assert result.peer.cohort.property_type == "office"


def test_predict_forwards_feature_primitives(tmp_path: Path) -> None:
    model = _FixedModel(log_value=0.0)
    registry = _build_registry(tmp_path, model=model, model_version="srv-v1", rmse=1.0)
    peers = _build_peer_registry(tmp_path)
    service = PredictionResourceService(registry, peers)

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
