"""Pillars for `app.schemas.PredictionResponse` and its nested models."""

from __future__ import annotations

from typing import Any

import pytest
from pydantic import ValidationError

from app.schemas import PredictionResponse


def _assert_field_error(exc: ValidationError, field_alias: str) -> None:
    locs = [".".join(str(x) for x in err["loc"]) for err in exc.errors()]
    assert any(field_alias in loc for loc in locs), (
        f"Expected error referencing {field_alias!r}, got locations: {locs}"
    )


class TestAcceptsCanonical:
    def test_accepts_canonical_example(self, valid_response_body: dict[str, Any]) -> None:
        model = PredictionResponse.model_validate(valid_response_body)
        assert model.id == "pred_sample_01"
        assert model.prediction.site_eui_kbtu_per_sqft == 87.3
        assert model.peer.percentile == 68
        assert model.ll97.at_risk is True


class TestStrictMode:
    def test_rejects_unknown_top_level_field(
        self, valid_response_body: dict[str, Any]
    ) -> None:
        body = {**valid_response_body, "extra": "nope"}

        with pytest.raises(ValidationError) as exc:
            PredictionResponse.model_validate(body)

        _assert_field_error(exc.value, "extra")


class TestIdField:
    def test_rejects_empty_id(self, valid_response_body: dict[str, Any]) -> None:
        body = {**valid_response_body, "id": ""}

        with pytest.raises(ValidationError) as exc:
            PredictionResponse.model_validate(body)

        _assert_field_error(exc.value, "id")


class TestGeneratedAtField:
    def test_accepts_iso_8601(self, valid_response_body: dict[str, Any]) -> None:
        body = {**valid_response_body, "generatedAt": "2026-04-16T14:30:00+00:00"}
        PredictionResponse.model_validate(body)

    def test_rejects_non_datetime_string(self, valid_response_body: dict[str, Any]) -> None:
        body = {**valid_response_body, "generatedAt": "not-a-date"}

        with pytest.raises(ValidationError) as exc:
            PredictionResponse.model_validate(body)

        _assert_field_error(exc.value, "generatedAt")


class TestInputNested:
    def test_input_is_validated_as_create_building_input(
        self, valid_response_body: dict[str, Any]
    ) -> None:
        body = {**valid_response_body, "input": {**valid_response_body["input"], "yearBuilt": 1799}}

        with pytest.raises(ValidationError) as exc:
            PredictionResponse.model_validate(body)

        _assert_field_error(exc.value, "yearBuilt")


class TestPredictionNested:
    def test_model_version_rejects_empty_string(
        self, valid_response_body: dict[str, Any]
    ) -> None:
        body = {
            **valid_response_body,
            "prediction": {**valid_response_body["prediction"], "modelVersion": ""},
        }

        with pytest.raises(ValidationError) as exc:
            PredictionResponse.model_validate(body)

        _assert_field_error(exc.value, "modelVersion")


class TestPeerPercentile:
    def test_rejects_below_0(self, valid_response_body: dict[str, Any]) -> None:
        body = {
            **valid_response_body,
            "peer": {**valid_response_body["peer"], "percentile": -1},
        }

        with pytest.raises(ValidationError) as exc:
            PredictionResponse.model_validate(body)

        _assert_field_error(exc.value, "percentile")

    def test_rejects_above_100(self, valid_response_body: dict[str, Any]) -> None:
        body = {
            **valid_response_body,
            "peer": {**valid_response_body["peer"], "percentile": 101},
        }

        with pytest.raises(ValidationError) as exc:
            PredictionResponse.model_validate(body)

        _assert_field_error(exc.value, "percentile")

    def test_accepts_boundary_0(self, valid_response_body: dict[str, Any]) -> None:
        body = {
            **valid_response_body,
            "peer": {**valid_response_body["peer"], "percentile": 0},
        }
        PredictionResponse.model_validate(body)

    def test_accepts_boundary_100(self, valid_response_body: dict[str, Any]) -> None:
        body = {
            **valid_response_body,
            "peer": {**valid_response_body["peer"], "percentile": 100},
        }
        PredictionResponse.model_validate(body)


class TestPeerCohortSize:
    def test_rejects_negative(self, valid_response_body: dict[str, Any]) -> None:
        body = {
            **valid_response_body,
            "peer": {**valid_response_body["peer"], "cohortSize": -1},
        }

        with pytest.raises(ValidationError) as exc:
            PredictionResponse.model_validate(body)

        _assert_field_error(exc.value, "cohortSize")


class TestPeerCohortAgeBand:
    @pytest.mark.parametrize(
        "age_band", ["pre-1950", "1950-1979", "1980-1999", "2000-plus"]
    )
    def test_accepts_every_enum_value(
        self, valid_response_body: dict[str, Any], age_band: str
    ) -> None:
        body = {
            **valid_response_body,
            "peer": {
                **valid_response_body["peer"],
                "cohort": {**valid_response_body["peer"]["cohort"], "ageBand": age_band},
            },
        }
        PredictionResponse.model_validate(body)

    def test_rejects_value_outside_enum(self, valid_response_body: dict[str, Any]) -> None:
        body = {
            **valid_response_body,
            "peer": {
                **valid_response_body["peer"],
                "cohort": {**valid_response_body["peer"]["cohort"], "ageBand": "ancient"},
            },
        }

        with pytest.raises(ValidationError) as exc:
            PredictionResponse.model_validate(body)

        _assert_field_error(exc.value, "ageBand")


class TestLL97AtRiskStrict:
    def test_rejects_truthy_string(self, valid_response_body: dict[str, Any]) -> None:
        body = {
            **valid_response_body,
            "ll97": {**valid_response_body["ll97"], "atRisk": "true"},
        }

        with pytest.raises(ValidationError) as exc:
            PredictionResponse.model_validate(body)

        _assert_field_error(exc.value, "atRisk")

    def test_rejects_integer(self, valid_response_body: dict[str, Any]) -> None:
        body = {
            **valid_response_body,
            "ll97": {**valid_response_body["ll97"], "atRisk": 1},
        }

        with pytest.raises(ValidationError) as exc:
            PredictionResponse.model_validate(body)

        _assert_field_error(exc.value, "atRisk")


class TestWireFormat:
    def test_serializes_every_key_in_camelcase(
        self, valid_response_body: dict[str, Any]
    ) -> None:
        model = PredictionResponse.model_validate(valid_response_body)
        dumped = model.model_dump(by_alias=True, mode="json")

        def assert_no_snake(d: Any, path: str = "") -> None:
            if isinstance(d, dict):
                for k, v in d.items():
                    assert "_" not in k, f"snake_case key at {path}.{k}"
                    assert_no_snake(v, f"{path}.{k}")
            elif isinstance(d, list):
                for i, v in enumerate(d):
                    assert_no_snake(v, f"{path}[{i}]")

        assert_no_snake(dumped)

    def test_round_trip_validate_then_dump(
        self, valid_response_body: dict[str, Any]
    ) -> None:
        model = PredictionResponse.model_validate(valid_response_body)
        dumped = model.model_dump(by_alias=True, mode="json")
        model2 = PredictionResponse.model_validate(dumped)
        assert model2.model_dump(by_alias=True, mode="json") == dumped

    def test_ll97_cap_fields_serialize_with_capital_to(
        self, valid_response_body: dict[str, Any]
    ) -> None:
        # Pins the Contract's camelCase normalization: "To" capitalized so the
        # alias generator round-trips cleanly.
        model = PredictionResponse.model_validate(valid_response_body)
        dumped = model.model_dump(by_alias=True, mode="json")
        assert "capKbtuPerSqft2024To2029" in dumped["ll97"]
        assert "capKbtuPerSqft2030To2034" in dumped["ll97"]
