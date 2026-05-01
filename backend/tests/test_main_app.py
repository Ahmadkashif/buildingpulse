"""Pillars for `app.main` — FastAPI instance, CORS, OpenAPI schema."""

from __future__ import annotations

from fastapi.testclient import TestClient


class TestAppConstruction:
    def test_app_module_imports_without_raising(self) -> None:
        import app.main  # noqa: F401  # import-time errors would raise here

    def test_app_exposes_predictions_route(self) -> None:
        from app.main import app  # type: ignore[attr-defined]

        routes = [(r.path, r.methods) for r in app.routes if hasattr(r, "methods")]
        assert any(
            path == "/api/predictions" and methods and "POST" in methods for path, methods in routes
        )


class TestCors:
    def test_preflight_from_localhost_3000_is_allowed(self, client: TestClient) -> None:
        response = client.options(
            "/api/predictions",
            headers={
                "Origin": "http://localhost:3000",
                "Access-Control-Request-Method": "POST",
                "Access-Control-Request-Headers": "content-type",
            },
        )
        assert response.headers.get("access-control-allow-origin") == "http://localhost:3000"

    def test_preflight_from_unrelated_origin_is_not_allowed(self, client: TestClient) -> None:
        response = client.options(
            "/api/predictions",
            headers={
                "Origin": "http://evil.example",
                "Access-Control-Request-Method": "POST",
                "Access-Control-Request-Headers": "content-type",
            },
        )
        # Either no ACAO header, or it doesn't echo evil.example — both acceptable.
        acao = response.headers.get("access-control-allow-origin")
        assert acao != "http://evil.example"


class TestOpenApi:
    def test_openapi_schema_lists_predictions_endpoint(self, client: TestClient) -> None:
        schema = client.get("/openapi.json").json()
        assert "/api/predictions" in schema["paths"]
        assert "post" in schema["paths"]["/api/predictions"]

    def test_openapi_request_body_references_create_building_input(
        self, client: TestClient
    ) -> None:
        schema = client.get("/openapi.json").json()
        post_op = schema["paths"]["/api/predictions"]["post"]
        request_ref = post_op["requestBody"]["content"]["application/json"]["schema"].get(
            "$ref", ""
        )
        assert "CreateBuildingInput" in request_ref

    def test_openapi_201_response_references_prediction_response(self, client: TestClient) -> None:
        schema = client.get("/openapi.json").json()
        post_op = schema["paths"]["/api/predictions"]["post"]
        responses = post_op["responses"]
        assert "201" in responses
        ref = responses["201"]["content"]["application/json"]["schema"].get("$ref", "")
        # The response is wrapped as `{"data": PredictionResponse}`; the wrapper
        # schema is allowed to live under any name so long as `PredictionResponse`
        # appears transitively in the schema components.
        components = schema.get("components", {}).get("schemas", {})
        assert "PredictionResponse" in components, (
            "PredictionResponse must appear in OpenAPI components.schemas"
        )
        assert ref, "201 response must reference a schema"
