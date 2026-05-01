"""Pure EUI predictor.

Wraps a fitted sklearn ``Pipeline`` that was trained on ``log1p(site_eui)``
with the columns ``[property_type, borough, gross_floor_area_sqft,
year_built, number_of_buildings]`` (see ``training/train_baseline.py``).

The function is intentionally side-effect free: no I/O, no logging, no
clock reads. Construct a single-row DataFrame, run the pipeline, invert
the log transform, and bracket the point estimate with a symmetric
``±INTERVAL_K_RMSE * rmse`` band derived from ``metrics.json``.
"""

from __future__ import annotations

from typing import Any, Protocol

import numpy as np
import pandas as pd

from app.domain.prediction.types import EuiPrediction

__all__ = ["FEATURE_COLUMNS", "INTERVAL_K_RMSE", "predict_eui"]

INTERVAL_K_RMSE: float = 1.5

FEATURE_COLUMNS: tuple[str, ...] = (
    "property_type",
    "borough",
    "gross_floor_area_sqft",
    "year_built",
    "number_of_buildings",
)


class _SupportsPredict(Protocol):
    def predict(self, x: Any) -> Any: ...


def predict_eui(
    *,
    model: _SupportsPredict,
    model_version: str,
    rmse: float,
    property_type: str,
    borough: str,
    gross_floor_area_sqft: int,
    year_built: int,
    number_of_buildings: int,
) -> EuiPrediction:
    """Run the trained pipeline and return point estimate + interval."""
    features = pd.DataFrame(
        [
            {
                "property_type": property_type,
                "borough": borough,
                "gross_floor_area_sqft": gross_floor_area_sqft,
                "year_built": year_built,
                "number_of_buildings": number_of_buildings,
            }
        ],
        columns=list(FEATURE_COLUMNS),
    )

    raw = np.asarray(model.predict(features))
    pred_log = float(raw.reshape(-1)[0])
    value = float(np.expm1(pred_log))

    half_width = INTERVAL_K_RMSE * float(rmse)
    return EuiPrediction(
        value=value,
        low=value - half_width,
        high=value + half_width,
        model_version=model_version,
    )
