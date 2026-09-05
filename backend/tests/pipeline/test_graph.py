"""LangGraph wiring: PDF goes through extract, JSON skips the LLM."""

from __future__ import annotations

from pathlib import Path

from tests.adapters.pdf_fixtures import cv_pdf_bytes
from tests.pipeline.fakes import FakeExtractor, deps, senior_backend_profile

from career_match.domain.models.enums import JobFamily, MatchBucket
from career_match.domain.models.profile import RawProfile
from career_match.domain.models.skill import RawSkill
from career_match.pipeline.graph import run_matching


def test_pdf_path_runs_extract_then_scores(tmp_path: Path) -> None:
    pdf_path = tmp_path / "cv.pdf"
    pdf_path.write_bytes(cv_pdf_bytes("Jane Python Kubernetes"))
    pipeline = deps(tmp_path)
    result = run_matching(pipeline, pdf_path, k=5)
    extractor = pipeline.extractor
    assert isinstance(extractor, FakeExtractor)
    assert extractor.calls == 1
    assert result["profile"].skill_by_id("kubernetes") is not None
    assert result["cards"][0].breakdown.bucket is MatchBucket.ELIGIBLE


def test_normalised_json_skips_extract(tmp_path: Path) -> None:
    path = tmp_path / "profile.json"
    path.write_text(senior_backend_profile().model_dump_json(), encoding="utf-8")
    pipeline = deps(tmp_path)
    result = run_matching(pipeline, path, k=5)
    extractor = pipeline.extractor
    assert isinstance(extractor, FakeExtractor)
    assert extractor.calls == 0
    assert result["profile"].profile_id == "p1"
    assert result["cards"][0].breakdown.bucket is MatchBucket.ELIGIBLE


def test_raw_json_skips_extract_but_still_normalises(tmp_path: Path) -> None:
    path = tmp_path / "raw.json"
    raw = RawProfile(
        first_name="Jane",
        target_families=[JobFamily.BACKEND],
        total_years_experience=6,
        skills=[RawSkill(label="Python"), RawSkill(label="K8s")],
    )
    path.write_text(raw.model_dump_json(), encoding="utf-8")
    pipeline = deps(tmp_path)
    result = run_matching(pipeline, path, k=5)
    extractor = pipeline.extractor
    assert isinstance(extractor, FakeExtractor)
    assert extractor.calls == 0
    assert result["profile"].skill_by_id("kubernetes") is not None
    assert result["cards"][0].breakdown.bucket is MatchBucket.ELIGIBLE
