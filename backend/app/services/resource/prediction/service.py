"""Prediction resource service.

Composes the EUI predictor with the peer-cohort lookup. Pulls the model,
model version, and RMSE from :class:`~app.repos.artifact_registry.ArtifactRegistry`,
runs :func:`app.domain.prediction.predictor.predict_eui`, then scores the
predicted EUI against the cohorts frame held by
:class:`~app.repos.peer_cohorts_registry.PeerCohortsRegistry` via
:func:`app.domain.peer.lookup.lookup`.
"""

from __future__ import annotations

from dataclasses import dataclass

from app.domain.peer import PeerOutlook, lookup
from app.domain.prediction import EuiPrediction, predict_eui
from app.repos.artifact_registry import ArtifactRegistry
from app.repos.peer_cohorts_registry import PeerCohortsRegistry

__all__ = ["PredictionResourceService", "PredictionResult"]


@dataclass(frozen=True, slots=True)
class PredictionResult:
    """Bundle returned by :meth:`PredictionResourceService.predict`."""

    eui: EuiPrediction
    peer: PeerOutlook


class PredictionResourceService:
    """Owns the `predict` verb on the prediction resource."""

    def __init__(
        self,
        registry: ArtifactRegistry,
        peer_cohorts: PeerCohortsRegistry,
    ) -> None:
        self._registry = registry
        self._peer_cohorts = peer_cohorts

    def predict(
        self,
        *,
        property_type: str,
        borough: str,
        gross_floor_area_sqft: int,
        year_built: int,
        number_of_buildings: int,
    ) -> PredictionResult:
        eui = predict_eui(
            model=self._registry.predictor,
            model_version=self._registry.model_version,
            rmse=self._registry.rmse,
            property_type=property_type,
            borough=borough,
            gross_floor_area_sqft=gross_floor_area_sqft,
            year_built=year_built,
            number_of_buildings=number_of_buildings,
        )
        peer = lookup(
            cohorts=self._peer_cohorts.cohorts,
            property_type=property_type,
            borough=borough,
            year_built=year_built,
            predicted_eui=eui.value,
        )
        return PredictionResult(eui=eui, peer=peer)
