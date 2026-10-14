"""GET/PUT /api/profile and POST /api/rematch. PUT does not rescore."""

from __future__ import annotations

from pathlib import Path

from fastapi.testclient import TestClient

from career_match.api.app import create_app
from career_match.domain.models.enums import MatchBucket, SkillLevel
from career_match.domain.models.skill import NormalizedSkill
from tests.pipeline.fakes import FakeExtractor, deps


def test_profile_requires_a_session(tmp_path: Path) -> None:
    client = TestClient(create_app(deps(tmp_path)))
    assert client.get("/api/profile").status_code == 404
    assert client.post("/api/rematch").status_code == 404


def test_match_then_get_and_put_profile(tmp_path: Path) -> None:
    client = TestClient(create_app(deps(tmp_path)))
    client.post("/api/match", json={"text": "Jane Python K8s", "k": 5})
    before = client.get("/api/profile")
    assert before.status_code == 200
    body = before.json()
    assert body["user_edited"] is False
    assert body["correction_count"] == 0
    cards_before = client.get("/api/offers").json()["cards"]

    body["target_title"] = "Staff backend"
    updated = client.put("/api/profile", json=body)
    assert updated.status_code == 200
    assert updated.json()["target_title"] == "Staff backend"
    assert updated.json()["user_edited"] is True
    assert updated.json()["correction_count"] == 1
    assert updated.json()["profile_id"] == body["profile_id"]
    assert client.get("/api/offers").json()["cards"] == cards_before


def test_rematch_skips_extract_and_uses_edits(tmp_path: Path) -> None:
    pipeline = deps(tmp_path)
    client = TestClient(create_app(pipeline))
    client.post("/api/match", json={"text": "Jane Python K8s", "k": 5})
    extractor = pipeline.extractor
    assert isinstance(extractor, FakeExtractor)
    assert extractor.calls == 1
    assert client.get("/api/offers").json()["cards"][0]["bucket"] == MatchBucket.ELIGIBLE.value

    profile = client.get("/api/profile").json()
    profile["skills"] = [NormalizedSkill(skill_id="python", level=SkillLevel.WORKING).model_dump()]
    client.put("/api/profile", json=profile)

    rematched = client.post("/api/rematch", params={"k": 5})
    assert rematched.status_code == 200
    assert extractor.calls == 1
    assert rematched.json()["cards"]
    assert rematched.json()["cards"][0]["bucket"] != MatchBucket.ELIGIBLE.value
    assert client.get("/api/offers").json()["cards"] == rematched.json()["cards"]
