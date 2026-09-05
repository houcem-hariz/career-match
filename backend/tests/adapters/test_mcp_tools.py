"""MCP tool bodies and server registration. Fakes only, no stdio session."""

from __future__ import annotations

import asyncio
from pathlib import Path

from career_match.adapters.mcp.server import TOOL_NAMES, create_server
from career_match.adapters.mcp.tools import (
    extract_profile,
    match_profile,
    normalize_profile,
    search_offers,
    simulate_course_impact,
)
from career_match.domain.models.enums import JobFamily, MatchBucket, SeniorityLevel, SkillLevel
from career_match.domain.models.profile import Profile, RawProfile
from career_match.domain.models.skill import NormalizedSkill, RawSkill
from tests.adapters.pdf_fixtures import cv_pdf_bytes
from tests.pipeline.fakes import FakeExtractor, deps, senior_backend_profile


def test_normalize_profile_resolves_k8s_alias(tmp_path: Path) -> None:
    raw = RawProfile(
        first_name="Jane",
        target_families=[JobFamily.BACKEND],
        total_years_experience=6,
        skills=[RawSkill(label="K8s")],
    )
    result = normalize_profile(deps(tmp_path), raw.model_dump(mode="json"))
    ids = {skill["skill_id"] for skill in result["profile"]["skills"]}
    assert "kubernetes" in ids


def test_extract_and_match_from_pdf(tmp_path: Path) -> None:
    pdf_path = tmp_path / "cv.pdf"
    pdf_path.write_bytes(cv_pdf_bytes("Jane Python Kubernetes"))
    pipeline = deps(tmp_path)
    extracted = extract_profile(pipeline, str(pdf_path))
    assert extracted["raw_profile"]["first_name"] == "Jane"
    matched = match_profile(pipeline, str(pdf_path), k=5)
    assert matched["cards"][0]["bucket"] == MatchBucket.ELIGIBLE.value
    extractor = pipeline.extractor
    assert isinstance(extractor, FakeExtractor)
    assert extractor.calls >= 1


def test_match_profile_json_skips_extract(tmp_path: Path) -> None:
    path = tmp_path / "profile.json"
    path.write_text(senior_backend_profile().model_dump_json(), encoding="utf-8")
    pipeline = deps(tmp_path)
    matched = match_profile(pipeline, str(path), k=5)
    extractor = pipeline.extractor
    assert isinstance(extractor, FakeExtractor)
    assert extractor.calls == 0
    assert matched["cards"][0]["source_id"] == "good"


def test_search_offers_returns_hits(tmp_path: Path) -> None:
    result = search_offers(
        deps(tmp_path),
        senior_backend_profile().model_dump(mode="json"),
        k=5,
    )
    assert result["candidate_count"] == 1
    assert result["hits"][0]["source_id"] == "good"


def test_simulate_course_moves_bucket(tmp_path: Path) -> None:
    profile = Profile(
        profile_id="p1",
        target_families=[JobFamily.BACKEND],
        seniority=SeniorityLevel.SENIOR,
        skills=[NormalizedSkill(skill_id="python", level=SkillLevel.WORKING)],
    )
    result = simulate_course_impact(
        deps(tmp_path),
        profile.model_dump(mode="json"),
        "good",
        "k8s-fundamentals",
        0.8,
    )
    assert result["delta"] > 0
    assert result["bucket_before"] == MatchBucket.REACHABLE.value
    assert result["bucket_after"] == MatchBucket.ELIGIBLE.value


def test_server_registers_the_five_tools(tmp_path: Path) -> None:
    server = create_server(deps(tmp_path))
    listed = asyncio.run(server.list_tools())
    names = {tool.name for tool in listed}
    assert set(TOOL_NAMES) <= names
