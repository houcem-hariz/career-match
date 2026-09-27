"""Guest session stores POST /api/match cards for later GET."""

from __future__ import annotations

from pathlib import Path

from fastapi.testclient import TestClient

from career_match.api.app import create_app
from career_match.api.session import COOKIE_NAME
from tests.pipeline.fakes import deps


def test_offers_require_a_prior_match(tmp_path: Path) -> None:
    client = TestClient(create_app(deps(tmp_path)))
    assert client.get("/api/offers").status_code == 404
    assert client.get("/api/offers/good").status_code == 404


def test_match_then_list_and_detail(tmp_path: Path) -> None:
    client = TestClient(create_app(deps(tmp_path)))
    matched = client.post("/api/match", json={"text": "Jane Python K8s", "k": 5})
    assert matched.status_code == 200
    assert COOKIE_NAME in client.cookies

    listed = client.get("/api/offers")
    assert listed.status_code == 200
    assert listed.json()["cards"] == matched.json()["cards"]

    detail = client.get("/api/offers/good")
    assert detail.status_code == 200
    assert detail.json()["source_id"] == "good"
    assert detail.json()["dimensions"] == matched.json()["cards"][0]["dimensions"]


def test_unknown_source_id_is_404(tmp_path: Path) -> None:
    client = TestClient(create_app(deps(tmp_path)))
    client.post("/api/match", json={"text": "Jane Python K8s", "k": 5})
    response = client.get("/api/offers/missing")
    assert response.status_code == 404
    assert "Unknown offer" in response.json()["detail"]


def test_sessions_do_not_share_cards(tmp_path: Path) -> None:
    app = create_app(deps(tmp_path))
    first = TestClient(app)
    second = TestClient(app)
    first.post("/api/match", json={"text": "Jane Python K8s", "k": 5})
    assert first.get("/api/offers").status_code == 200
    assert second.get("/api/offers").status_code == 404
