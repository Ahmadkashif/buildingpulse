"""Process-wide registry for ML artifacts.

Loads ``model.pkl`` (a fitted sklearn ``Pipeline``) and ``metrics.json`` once
at app startup. Construction is the load — missing files raise immediately,
so the FastAPI lifespan hook fails fast rather than letting the first
prediction request blow up.

A class-level counter tracks how many times the registry was constructed
in the current process; the prediction endpoint logs it so operators (and
the self-verification step in issue #56) can confirm a single load.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import joblib

_MODEL_FILE = "model.pkl"
_METRICS_FILE = "metrics.json"


class ArtifactRegistry:
    """Holds the trained predictor and its training metrics."""

    _load_count: int = 0

    def __init__(self, artifacts_dir: Path | str) -> None:
        directory = Path(artifacts_dir)
        model_path = directory / _MODEL_FILE
        metrics_path = directory / _METRICS_FILE

        if not model_path.is_file():
            raise FileNotFoundError(f"missing model artifact: {model_path}")
        if not metrics_path.is_file():
            raise FileNotFoundError(f"missing metrics artifact: {metrics_path}")

        self._predictor: Any = joblib.load(model_path)

        metrics = json.loads(metrics_path.read_text())
        try:
            self._model_version: str = str(metrics["modelVersion"])
            self._rmse: float = float(metrics["rmse"])
        except KeyError as exc:
            raise KeyError(f"metrics.json missing required key: {exc.args[0]}") from exc

        ArtifactRegistry._load_count += 1

    @property
    def predictor(self) -> Any:
        return self._predictor

    @property
    def model_version(self) -> str:
        return self._model_version

    @property
    def rmse(self) -> float:
        return self._rmse

    @classmethod
    def load_count(cls) -> int:
        return cls._load_count

    @classmethod
    def _reset_load_count(cls) -> None:
        """Test-only hook: reset the process-wide load counter."""
        cls._load_count = 0


__all__ = ["ArtifactRegistry"]
