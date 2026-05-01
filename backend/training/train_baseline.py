"""Baseline training pipeline.

CLI entry point: ``python -m training.train_baseline``.

Reads ``backend/data/dataset.csv``, cleans via :func:`training.clean.load_and_clean`,
splits 80/20 with ``random_state=42``, one-hot encodes ``property_type`` and
``borough``, fits :class:`~sklearn.linear_model.LinearRegression` on
``log1p(site_eui)``, and writes two artifacts under ``backend/artifacts/``:

* ``model.pkl``   — joblib dump of the full fitted ``Pipeline``.
* ``metrics.json`` — ``{r2, rmse, modelVersion, trainRows, testRows, trainedAt}``.

The script is deterministic: re-running it on the same input file produces
byte-identical ``metrics.json``. ``trainedAt`` is sourced from the input CSV's
mtime (overridable via ``SOURCE_DATE_EPOCH``) rather than the wall clock.
"""

from __future__ import annotations

import json
import os
from datetime import UTC, datetime
from pathlib import Path

import joblib
import numpy as np
from sklearn.compose import ColumnTransformer
from sklearn.linear_model import LinearRegression
from sklearn.metrics import r2_score, root_mean_squared_error
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder

from training.clean import load_and_clean

__all__ = ["main"]

_BACKEND_ROOT: Path = Path(__file__).resolve().parents[1]
_DATA_PATH: Path = _BACKEND_ROOT / "data" / "dataset.csv"
_ARTIFACTS_DIR: Path = _BACKEND_ROOT / "artifacts"
_MODEL_PATH: Path = _ARTIFACTS_DIR / "model.pkl"
_METRICS_PATH: Path = _ARTIFACTS_DIR / "metrics.json"

_MODEL_VERSION: str = "baseline-lr-v1"
_RANDOM_STATE: int = 42
_TEST_SIZE: float = 0.20

_CATEGORICAL: list[str] = ["property_type", "borough"]
_NUMERIC: list[str] = ["gross_floor_area_sqft", "year_built", "number_of_buildings"]
_TARGET: str = "site_eui"


def _resolve_trained_at() -> str:
    epoch_env = os.environ.get("SOURCE_DATE_EPOCH")
    epoch = float(epoch_env) if epoch_env is not None else _DATA_PATH.stat().st_mtime
    return datetime.fromtimestamp(int(epoch), tz=UTC).isoformat().replace("+00:00", "Z")


def _build_pipeline() -> Pipeline:
    pre = ColumnTransformer(
        transformers=[
            ("cat", OneHotEncoder(handle_unknown="ignore", sparse_output=False), _CATEGORICAL),
            ("num", "passthrough", _NUMERIC),
        ]
    )
    return Pipeline(steps=[("pre", pre), ("lr", LinearRegression())])


def main() -> None:
    df = load_and_clean(_DATA_PATH)

    features = df[_CATEGORICAL + _NUMERIC]
    target_log = np.log1p(df[_TARGET].to_numpy(dtype=float))

    x_train, x_test, y_train_log, y_test_log = train_test_split(
        features,
        target_log,
        test_size=_TEST_SIZE,
        random_state=_RANDOM_STATE,
    )

    pipeline = _build_pipeline()
    pipeline.fit(x_train, y_train_log)

    y_pred_log = pipeline.predict(x_test)
    y_pred = np.expm1(y_pred_log)
    y_test = np.expm1(y_test_log)

    r2 = float(r2_score(y_test, y_pred))
    rmse = float(root_mean_squared_error(y_test, y_pred))

    _ARTIFACTS_DIR.mkdir(parents=True, exist_ok=True)
    joblib.dump(pipeline, _MODEL_PATH)

    metrics = {
        "r2": round(r2, 6),
        "rmse": round(rmse, 6),
        "modelVersion": _MODEL_VERSION,
        "trainRows": int(len(x_train)),
        "testRows": int(len(x_test)),
        "trainedAt": _resolve_trained_at(),
    }
    _METRICS_PATH.write_text(json.dumps(metrics, indent=2, sort_keys=True) + "\n")


if __name__ == "__main__":
    main()
