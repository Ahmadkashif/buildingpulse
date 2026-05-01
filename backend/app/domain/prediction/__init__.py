"""Prediction domain package."""

from app.domain.prediction.predictor import predict_eui
from app.domain.prediction.types import EuiPrediction

__all__ = ["EuiPrediction", "predict_eui"]
