"""OpenAPI contract for POST /api/match is published at /openapi.json."""

from __future__ import annotations

from pathlib import Path

from fastapi.testclient import TestClient

from career_match.api.app import create_app
from tests.pipeline.fakes import deps


def test_openapi_documents_json_and_pdf_bodies(tmp_path: Path) -> None:
    spec = TestClient(create_app(deps(tmp_path))).get("/openapi.json").json()
    post = spec["paths"]["/api/match"]["post"]
    content = post["requestBody"]["content"]
    assert "application/json" in content
    assert "multipart/form-data" in content
    assert content["application/json"]["schema"]["$ref"].endswith("MatchJsonBody")
    assert "cv" in content["multipart/form-data"]["schema"]["properties"]

    schemas = spec["components"]["schemas"]
    assert "MatchJsonBody" in schemas
    assert "MatchResponse" in schemas
    assert "CardPayload" in schemas
    assert "ErrorBody" in schemas
    card_fields = schemas["CardPayload"]["properties"]
    for key in ("bucket", "score", "dimensions", "gaps", "simulations"):
        assert key in card_fields
    assert spec["paths"]["/api/offers"]["get"]["responses"]["200"]
    assert spec["paths"]["/api/offers/{source_id}"]["get"]["responses"]["200"]


def test_docs_ui_is_served(tmp_path: Path) -> None:
    client = TestClient(create_app(deps(tmp_path)))
    assert client.get("/docs").status_code == 200
    assert client.get("/redoc").status_code == 200
