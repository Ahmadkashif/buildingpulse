"""Unit tests for ArtifactRegistry.

Covers: successful load, missing model.pkl, missing metrics.json, malformed
metrics.json (missing required keys), typed access (predictor, model_version,
rmse), and the process-wide load counter.
"""

from __future__ import annotations

import json
from pathlib import Path

import joblib
import pytest
from app.repos.artifact_registry import ArtifactRegistry


def _write_artifacts(
    directory: Path,
    *,
    model_version: str = "baseline-lr-v1",
    rmse: float = 12.5,
    write_model: bool = True,
    write_metrics: bool = True,
    metrics_payload: dict[str, object] | None = None,
) -> None:
    if write_model:
        joblib.dump({"sentinel": "predictor"}, directory / "model.pkl")
    if write_metrics:
        payload: dict[str, object]
        if metrics_payload is not None:
            payload = metrics_payload
        else:
            payload = {
                "modelVersion": model_version,
                "rmse": rmse,
                "r2": 0.95,
                "trainRows": 100,
                "testRows": 25,
                "trainedAt": "2026-05-01T00:00:00Z",
            }
        (directory / "metrics.json").write_text(json.dumps(payload))


@pytest.fixture(autouse=True)
def _reset_counter() -> None:
    ArtifactRegistry._reset_load_count()


def test_loads_predictor_and_metrics(tmp_path: Path) -> None:
    _write_artifacts(tmp_path, model_version="m1", rmse=7.25)

    registry = ArtifactRegistry(tmp_path)

    assert registry.predictor == {"sentinel": "predictor"}
    assert registry.model_version == "m1"
    assert registry.rmse == 7.25


def test_accepts_directory_as_string(tmp_path: Path) -> None:
    _write_artifacts(tmp_path)

    registry = ArtifactRegistry(str(tmp_path))

    assert registry.model_version == "baseline-lr-v1"


def test_missing_model_raises_filenotfounderror(tmp_path: Path) -> None:
    _write_artifacts(tmp_path, write_model=False)

    with pytest.raises(FileNotFoundError, match="model artifact"):
        ArtifactRegistry(tmp_path)


def test_missing_metrics_raises_filenotfounderror(tmp_path: Path) -> None:
    _write_artifacts(tmp_path, write_metrics=False)

    with pytest.raises(FileNotFoundError, match="metrics artifact"):
        ArtifactRegistry(tmp_path)


def test_metrics_missing_required_key_raises_keyerror(tmp_path: Path) -> None:
    _write_artifacts(tmp_path, metrics_payload={"rmse": 1.0})

    with pytest.raises(KeyError, match="modelVersion"):
        ArtifactRegistry(tmp_path)


def test_load_count_increments_per_construction(tmp_path: Path) -> None:
    _write_artifacts(tmp_path)

    assert ArtifactRegistry.load_count() == 0
    ArtifactRegistry(tmp_path)
    assert ArtifactRegistry.load_count() == 1
    ArtifactRegistry(tmp_path)
    assert ArtifactRegistry.load_count() == 2
