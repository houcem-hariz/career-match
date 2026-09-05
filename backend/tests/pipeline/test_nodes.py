"""Pipeline nodes wrap week-3 functions. No Postgres, no live LLM, no graph yet."""

from __future__ import annotations

from pathlib import Path

import pytest
from tests.adapters.pdf_fixtures import cv_pdf_bytes
from tests.pipeline.fakes import deps, eligible_offer, senior_backend_profile

from career_match.domain.models.enums import JobFamily, MatchBucket, SeniorityLevel
from career_match.domain.models.profile import RawProfile
from career_match.domain.models.skill import RawSkill
from career_match.pipeline.nodes import extract_node, normalize_node, retrieve_node, score_node
from career_match.pipeline.state import MatchState


def test_extract_node_fills_raw_profile(tmp_path: Path) -> None:
    pdf_path = tmp_path / "cv.pdf"
    pdf_path.write_bytes(cv_pdf_bytes("Jane Doe Senior Backend Engineer"))
    state: MatchState = {"source_path": str(pdf_path), "k": 5}
    patch = extract_node(state, deps(tmp_path))
    assert patch["raw_profile"].first_name == "Jane"
    assert patch["extracted_from_cache"] is False
    assert len(patch["source_cv_hash"]) == 64


def test_normalize_node_resolves_k8s_alias(tmp_path: Path) -> None:
    state: MatchState = {
        "raw_profile": RawProfile(
            first_name="Jane",
            target_families=[JobFamily.BACKEND],
            total_years_experience=6,
            skills=[RawSkill(label="K8s")],
        )
    }
    patch = normalize_node(state, deps(tmp_path))
    profile = patch["profile"]
    assert profile.skill_by_id("kubernetes") is not None
    assert profile.seniority is SeniorityLevel.SENIOR


def test_retrieve_and_score_nodes_match_week_three(tmp_path: Path) -> None:
    pipeline = deps(tmp_path)
    state: MatchState = {"k": 5, "profile": senior_backend_profile()}
    state = {**state, **retrieve_node(state, pipeline)}
    state = {**state, **score_node(state, pipeline)}
    assert state["candidate_count"] == 1
    assert state["cards"][0].breakdown.bucket is MatchBucket.ELIGIBLE
    assert state["cards"][0].breakdown.total > 70


def test_full_node_chain_from_pdf(tmp_path: Path) -> None:
    pdf_path = tmp_path / "cv.pdf"
    pdf_path.write_bytes(cv_pdf_bytes("Jane Python Kubernetes"))
    pipeline = deps(tmp_path)
    state: MatchState = {"source_path": str(pdf_path), "k": 5}
    state = {**state, **extract_node(state, pipeline)}
    state = {**state, **normalize_node(state, pipeline)}
    state = {**state, **retrieve_node(state, pipeline)}
    state = {**state, **score_node(state, pipeline)}
    assert state["profile"].skill_by_id("python") is not None
    assert state["profile"].skill_by_id("kubernetes") is not None
    assert state["cards"][0].breakdown.bucket is MatchBucket.ELIGIBLE


def test_normalize_node_requires_raw_profile(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="raw_profile"):
        normalize_node({}, deps(tmp_path, eligible_offer()))
