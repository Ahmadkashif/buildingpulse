"""Pillars for the validation path of `POST /api/predictions`.

All failures should surface as HTTP 422 (FastAPI default for Pydantic
validation) with a body that names the offending field so clients can surface
per-field errors.
"""

from __future__ import annotations

from typing import Any

import pytest
from fastapi.testclient import TestClient


def _assert_422_references_field(response_json: dict[str, Any], field_alias: str) -> None:
    """The FastAPI 422 envelope is `{"detail": [{"loc": [...], ...}, ...]}`."""
    detail = response_json.get("detail")
    assert isinstance(detail, list), f"Expected `detail` list, got: {response_json}"
    locs = [".".join(str(x) for x in item["loc"]) for item in detail]
    assert any(field_alias in loc for loc in locs), (
        f"Expected 422 to reference {field_alias!r}; loc paths were: {locs}"
    )


class TestMissingFields:
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
    def test_returns_422_on_missing_field(
        self,
        client: TestClient,
        valid_request_body: dict[str, Any],
        missing_field: str,
    ) -> None:
        body = dict(valid_request_body)
        del body[missing_field]

        response = client.post("/api/predictions", json=body)

        assert response.status_code == 422
        _assert_422_references_field(response.json(), missing_field)


class TestEnumViolations:
    def test_returns_422_on_invalid_property_type(
        self, client: TestClient, valid_request_body: dict[str, Any]
    ) -> None:
        body = {**valid_request_body, "propertyType": "castle"}
        response = client.post("/api/predictions", json=body)

        assert response.status_code == 422
        _assert_422_references_field(response.json(), "propertyType")

    def test_returns_422_on_invalid_borough(
        self, client: TestClient, valid_request_body: dict[str, Any]
    ) -> None:
        body = {**valid_request_body, "borough": "jersey-city"}
        response = client.post("/api/predictions", json=body)

        assert response.status_code == 422
        _assert_422_references_field(response.json(), "borough")


class TestNumericBoundaries:
    @pytest.mark.parametrize(
        ("field", "bad_value"),
        [
            ("yearBuilt", 1799),
            ("yearBuilt", 2027),
            ("grossFloorAreaSqft", 499),
            ("grossFloorAreaSqft", 5_000_001),
            ("numberOfBuildings", 0),
            ("numberOfBuildings", 11),
        ],
    )
    def test_returns_422_on_out_of_range(
        self,
        client: TestClient,
        valid_request_body: dict[str, Any],
        field: str,
        bad_value: int,
    ) -> None:
        body = {**valid_request_body, field: bad_value}
        response = client.post("/api/predictions", json=body)

        assert response.status_code == 422
        _assert_422_references_field(response.json(), field)


class TestStrictMode:
    def test_returns_422_on_unknown_field(
        self, client: TestClient, valid_request_body: dict[str, Any]
    ) -> None:
        body = {**valid_request_body, "mysteryField": 1}
        response = client.post("/api/predictions", json=body)

        assert response.status_code == 422
        _assert_422_references_field(response.json(), "mysteryField")
