"""Prediction resource service.

Thin orchestration over :func:`app.domain.prediction.predictor.predict_eui`:
pulls the model, model version, and RMSE from the
:class:`~app.repos.artifact_registry.ArtifactRegistry` and forwards the
caller-supplied feature primitives to the pure domain function.
"""

from __future__ import annotations

from app.domain.prediction import EuiPrediction, predict_eui
from app.repos.artifact_registry import ArtifactRegistry

__all__ = ["PredictionResourceService"]


class PredictionResourceService:
    """Owns the `predict` verb on the prediction resource."""

    def __init__(self, registry: ArtifactRegistry) -> None:
        self._registry = registry

    def predict(
        self,
        *,
        property_type: str,
        borough: str,
        gross_floor_area_sqft: int,
        year_built: int,
        number_of_buildings: int,
    ) -> EuiPrediction:
        return predict_eui(
            model=self._registry.predictor,
            model_version=self._registry.model_version,
            rmse=self._registry.rmse,
            property_type=property_type,
            borough=borough,
            gross_floor_area_sqft=gross_floor_area_sqft,
            year_built=year_built,
            number_of_buildings=number_of_buildings,
        )
