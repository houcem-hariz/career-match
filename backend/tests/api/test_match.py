"""POST /api/match wraps run_matching. Fakes only, no Postgres, no live LLM."""

from __future__ import annotations

from pathlib import Path

from fastapi.testclient import TestClient

from career_match.api.app import create_app
from career_match.domain.models.enums import MatchBucket
from tests.adapters.pdf_fixtures import cv_pdf_bytes
from tests.pipeline.fakes import FakeExtractor, deps


def test_match_pdf_returns_card_payload(tmp_path: Path) -> None:
    pipeline = deps(tmp_path)
    client = TestClient(create_app(pipeline))
    pdf = cv_pdf_bytes("Jane Python Kubernetes")
    response = client.post(
        "/api/match",
        params={"k": 5},
        files={"cv": ("cv.pdf", pdf, "application/pdf")},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["cards"][0]["bucket"] == MatchBucket.ELIGIBLE.value
    assert body["cards"][0]["source_id"] == "good"
    assert "dimensions" in body["cards"][0]
    assert "gaps" in body["cards"][0]
    assert "simulations" in body["cards"][0]
    extractor = pipeline.extractor
    assert isinstance(extractor, FakeExtractor)
    assert extractor.calls == 1


def test_match_text_returns_same_envelope(tmp_path: Path) -> None:
    pipeline = deps(tmp_path)
    client = TestClient(create_app(pipeline))
    response = client.post("/api/match", json={"text": "Jane Python K8s", "k": 5})
    assert response.status_code == 200
    body = response.json()
    assert body["cards"][0]["bucket"] == MatchBucket.ELIGIBLE.value
    extractor = pipeline.extractor
    assert isinstance(extractor, FakeExtractor)
    assert extractor.calls == 1


def test_match_example_uses_provided_pdf(tmp_path: Path) -> None:
    pdf_path = tmp_path / "jane.pdf"
    pdf_path.write_bytes(cv_pdf_bytes("Jane Python Kubernetes"))
    pipeline = deps(tmp_path)
    client = TestClient(
        create_app(pipeline, examples={"jane_doe_backend": pdf_path}),
    )
    response = client.post("/api/match", json={"example": "jane_doe_backend", "k": 5})
    assert response.status_code == 200
    assert response.json()["cards"][0]["source_id"] == "good"


def test_match_rejects_missing_source(tmp_path: Path) -> None:
    client = TestClient(create_app(deps(tmp_path)))
    response = client.post("/api/match", json={})
    assert response.status_code == 400
    assert "exactly one" in response.json()["detail"]


def test_match_rejects_two_sources(tmp_path: Path) -> None:
    client = TestClient(create_app(deps(tmp_path)))
    response = client.post(
        "/api/match",
        json={"text": "Jane", "example": "jane_doe_backend"},
    )
    assert response.status_code == 400


def test_match_rejects_unknown_example(tmp_path: Path) -> None:
    client = TestClient(create_app(deps(tmp_path)))
    response = client.post("/api/match", json={"example": "nope"})
    assert response.status_code == 400
    assert "Unknown example" in response.json()["detail"]
