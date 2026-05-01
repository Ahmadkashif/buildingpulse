"""Pillars for `app.schemas.CreateBuildingInput`.

Each test asserts exactly one pillar from PHASE1_PILLARS.md. Pydantic
validation errors are matched by field name — structural, not message-string —
so tests survive Pydantic error-message churn.
"""

from __future__ import annotations

from typing import Any

import pytest
from app.schemas import Borough, CreateBuildingInput, PropertyType
from pydantic import ValidationError


def _assert_field_error(exc: ValidationError, field_alias: str) -> None:
    """Assert that the ValidationError references the given camelCase field."""
    locs = [".".join(str(x) for x in err["loc"]) for err in exc.errors()]
    assert any(field_alias in loc for loc in locs), (
        f"Expected error referencing {field_alias!r}, got locations: {locs}"
    )


class TestAcceptsCanonical:
    def test_accepts_canonical_example(self, valid_request_body: dict[str, Any]) -> None:
        model = CreateBuildingInput.model_validate(valid_request_body)
        assert model.property_type == "multifamily-housing"
        assert model.borough == "brooklyn"
        assert model.gross_floor_area_sqft == 45000
        assert model.year_built == 1925
        assert model.number_of_buildings == 1


class TestRequiredFields:
    @pytest.mark.parametrize(
        "missing_field",
        [
            "propertyType",
            "borough",
            "grossFloorAreaSqft",
            "yearBuilt",
            "numberOfBuildings",
        ],
    )
    def test_rejects_missing_required_field(
        self, valid_request_body: dict[str, Any], missing_field: str
    ) -> None:
        body = dict(valid_request_body)
        del body[missing_field]

        with pytest.raises(ValidationError) as exc:
            CreateBuildingInput.model_validate(body)

        _assert_field_error(exc.value, missing_field)


class TestStrictMode:
    def test_rejects_unknown_field(self, valid_request_body: dict[str, Any]) -> None:
        body = {**valid_request_body, "nonsense": 1}

        with pytest.raises(ValidationError) as exc:
            CreateBuildingInput.model_validate(body)

        _assert_field_error(exc.value, "nonsense")


class TestEnumPropertyType:
    @pytest.mark.parametrize(
        "value",
        [
            "multifamily-housing",
            "office",
            "hotel",
            "retail",
            "hospital",
            "mixed-use",
        ],
    )
    def test_accepts_every_enum_value(
        self, valid_request_body: dict[str, Any], value: PropertyType
    ) -> None:
        body = {**valid_request_body, "propertyType": value}
        CreateBuildingInput.model_validate(body)

    def test_rejects_value_outside_enum(self, valid_request_body: dict[str, Any]) -> None:
        body = {**valid_request_body, "propertyType": "castle"}

        with pytest.raises(ValidationError) as exc:
            CreateBuildingInput.model_validate(body)

        _assert_field_error(exc.value, "propertyType")


class TestEnumBorough:
    @pytest.mark.parametrize(
        "value",
        ["manhattan", "brooklyn", "queens", "bronx", "staten-island"],
    )
    def test_accepts_every_enum_value(
        self, valid_request_body: dict[str, Any], value: Borough
    ) -> None:
        body = {**valid_request_body, "borough": value}
        CreateBuildingInput.model_validate(body)

    def test_rejects_value_outside_enum(self, valid_request_body: dict[str, Any]) -> None:
        body = {**valid_request_body, "borough": "jersey-city"}

        with pytest.raises(ValidationError) as exc:
            CreateBuildingInput.model_validate(body)

        _assert_field_error(exc.value, "borough")


class TestYearBuiltBounds:
    def test_rejects_below_1800(self, valid_request_body: dict[str, Any]) -> None:
        body = {**valid_request_body, "yearBuilt": 1799}

        with pytest.raises(ValidationError) as exc:
            CreateBuildingInput.model_validate(body)

        _assert_field_error(exc.value, "yearBuilt")

    def test_rejects_above_2026(self, valid_request_body: dict[str, Any]) -> None:
        body = {**valid_request_body, "yearBuilt": 2027}

        with pytest.raises(ValidationError) as exc:
            CreateBuildingInput.model_validate(body)

        _assert_field_error(exc.value, "yearBuilt")

    def test_accepts_lower_boundary_1800(self, valid_request_body: dict[str, Any]) -> None:
        body = {**valid_request_body, "yearBuilt": 1800}
        CreateBuildingInput.model_validate(body)

    def test_accepts_upper_boundary_2026(self, valid_request_body: dict[str, Any]) -> None:
        body = {**valid_request_body, "yearBuilt": 2026}
        CreateBuildingInput.model_validate(body)


class TestGrossFloorAreaBounds:
    def test_rejects_below_500(self, valid_request_body: dict[str, Any]) -> None:
        body = {**valid_request_body, "grossFloorAreaSqft": 499}

        with pytest.raises(ValidationError) as exc:
            CreateBuildingInput.model_validate(body)

        _assert_field_error(exc.value, "grossFloorAreaSqft")

    def test_rejects_above_5_000_000(self, valid_request_body: dict[str, Any]) -> None:
        body = {**valid_request_body, "grossFloorAreaSqft": 5_000_001}

        with pytest.raises(ValidationError) as exc:
            CreateBuildingInput.model_validate(body)

        _assert_field_error(exc.value, "grossFloorAreaSqft")

    def test_accepts_lower_boundary_500(self, valid_request_body: dict[str, Any]) -> None:
        body = {**valid_request_body, "grossFloorAreaSqft": 500}
        CreateBuildingInput.model_validate(body)

    def test_accepts_upper_boundary_5_000_000(self, valid_request_body: dict[str, Any]) -> None:
        body = {**valid_request_body, "grossFloorAreaSqft": 5_000_000}
        CreateBuildingInput.model_validate(body)

    def test_rejects_float_no_coercion(self, valid_request_body: dict[str, Any]) -> None:
        body = {**valid_request_body, "grossFloorAreaSqft": 45000.5}

        with pytest.raises(ValidationError) as exc:
            CreateBuildingInput.model_validate(body)

        _assert_field_error(exc.value, "grossFloorAreaSqft")


class TestNumberOfBuildingsBounds:
    def test_rejects_below_1(self, valid_request_body: dict[str, Any]) -> None:
        body = {**valid_request_body, "numberOfBuildings": 0}

        with pytest.raises(ValidationError) as exc:
            CreateBuildingInput.model_validate(body)

        _assert_field_error(exc.value, "numberOfBuildings")

    def test_rejects_above_10(self, valid_request_body: dict[str, Any]) -> None:
        body = {**valid_request_body, "numberOfBuildings": 11}

        with pytest.raises(ValidationError) as exc:
            CreateBuildingInput.model_validate(body)

        _assert_field_error(exc.value, "numberOfBuildings")

    def test_accepts_boundary_1(self, valid_request_body: dict[str, Any]) -> None:
        body = {**valid_request_body, "numberOfBuildings": 1}
        CreateBuildingInput.model_validate(body)

    def test_accepts_boundary_10(self, valid_request_body: dict[str, Any]) -> None:
        body = {**valid_request_body, "numberOfBuildings": 10}
        CreateBuildingInput.model_validate(body)


class TestWireFormat:
    def test_parses_camelcase_keys(self, valid_request_body: dict[str, Any]) -> None:
        # valid_request_body uses camelCase already; this pins that the model
        # reads camelCase (not the Python snake_case attribute names) on input.
        model = CreateBuildingInput.model_validate(valid_request_body)
        assert model.property_type == valid_request_body["propertyType"]
        assert model.gross_floor_area_sqft == valid_request_body["grossFloorAreaSqft"]

    def test_rejects_snake_case_keys_on_input(self) -> None:
        # The wire format is camelCase only. Snake-case JSON (e.g. from a
        # mistaken client) must be rejected so the Contract has one format.
        snake_body = {
            "property_type": "multifamily-housing",
            "borough": "brooklyn",
            "gross_floor_area_sqft": 45000,
            "year_built": 1925,
            "number_of_buildings": 1,
        }
        with pytest.raises(ValidationError):
            CreateBuildingInput.model_validate(snake_body)

    def test_serializes_camelcase_keys(self, valid_request_body: dict[str, Any]) -> None:
        model = CreateBuildingInput.model_validate(valid_request_body)
        dumped = model.model_dump(by_alias=True)
        assert set(dumped.keys()) == {
            "propertyType",
            "borough",
            "grossFloorAreaSqft",
            "yearBuilt",
            "numberOfBuildings",
        }
