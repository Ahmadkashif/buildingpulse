"""Pillars for `app.fixtures.stub_prediction`.

The stub is the only source of `prediction`, `peer`, `ll97` data in Phase 1.
It must always be schema-valid, because the handler hands it back verbatim.
"""

from __future__ import annotations

from app.schemas import CreateBuildingInput, PredictionResponse


class TestStubValidity:
    def test_stub_validates_against_prediction_response(self) -> None:
        from app.fixtures.stub_prediction import STUB  # type: ignore[attr-defined]

        PredictionResponse.model_validate(STUB)

    def test_stub_input_validates_against_create_building_input(self) -> None:
        from app.fixtures.stub_prediction import STUB  # type: ignore[attr-defined]

        CreateBuildingInput.model_validate(STUB["input"])


class TestStubIntent:
    def test_stub_model_version_is_baseline_lr_v1(self) -> None:
        """Pins the stub's modelVersion — Phase 1 must not drift from the Contract example."""
        from app.fixtures.stub_prediction import STUB  # type: ignore[attr-defined]

        assert STUB["prediction"]["modelVersion"] == "baseline-lr-v1"
