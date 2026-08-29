"""Extraction cache and CV orchestration, without calling a live LLM."""

from __future__ import annotations

from pathlib import Path

import pytest

from career_match.adapters.extraction.service import extract_cv
from career_match.adapters.llm.prompts import parse_profile_payload
from career_match.adapters.llm.protocol import PROMPT_VERSION
from career_match.adapters.parsing.pdf import EmptyPdfError, extract_text
from career_match.adapters.storage.extraction_cache import ExtractionCache
from career_match.domain.models.profile import RawProfile
from tests.adapters.pdf_fixtures import cv_pdf_bytes


class FakeExtractor:
    def __init__(self) -> None:
        self.calls = 0
        self.model_id = "fake-extractor"

    def extract_profile(self, cv_text: str) -> RawProfile:
        self.calls += 1
        first = cv_text.split()[0] if cv_text.split() else None
        return RawProfile(first_name=first, target_title="Backend Engineer")


def test_extract_text_reads_selectable_pdf() -> None:
    pdf = cv_pdf_bytes("Jane Doe Python Django")
    assert "Jane Doe" in extract_text(pdf)
    assert "Python" in extract_text(pdf)


def test_empty_pdf_is_rejected() -> None:
    pdf = cv_pdf_bytes("")
    with pytest.raises(EmptyPdfError):
        extract_text(pdf)


def test_cache_roundtrip(tmp_path: Path) -> None:
    cache = ExtractionCache(tmp_path)
    key = cache.key(b"cv-bytes", PROMPT_VERSION, "openai/gpt-oss-20b")
    assert cache.get(key) is None
    cache.put(key, {"first_name": "Jane"})
    assert cache.get(key) == {"first_name": "Jane"}


def test_cache_disabled_never_reads_or_writes(tmp_path: Path) -> None:
    cache = ExtractionCache(tmp_path, enabled=False)
    key = cache.key(b"cv-bytes", PROMPT_VERSION, "model")
    cache.put(key, {"first_name": "Jane"})
    assert cache.get(key) is None
    assert not list(tmp_path.iterdir())


def test_extract_cv_uses_cache_on_second_call(tmp_path: Path) -> None:
    pdf_path = tmp_path / "cv.pdf"
    pdf_path.write_bytes(cv_pdf_bytes("Jane Doe Senior Backend Engineer"))
    cache = ExtractionCache(tmp_path / "cache")
    extractor = FakeExtractor()

    first, from_cache = extract_cv(pdf_path, extractor, cache, "openai/gpt-oss-20b")
    second, second_from_cache = extract_cv(pdf_path, extractor, cache, "openai/gpt-oss-20b")

    assert from_cache is False
    assert second_from_cache is True
    assert extractor.calls == 1
    assert first.first_name == second.first_name == "Jane"


def test_prompt_or_model_change_busts_cache(tmp_path: Path) -> None:
    cache = ExtractionCache(tmp_path)
    payload = b"same-cv"
    key_a = cache.key(payload, "cv-raw-v1", "openai/gpt-oss-20b")
    key_b = cache.key(payload, "cv-raw-v2", "openai/gpt-oss-20b")
    key_c = cache.key(payload, "cv-raw-v1", "other-model")
    assert len({key_a, key_b, key_c}) == 3


def test_extract_cv_is_provider_agnostic(tmp_path: Path) -> None:
    """The orchestration layer must not care which extractor implementation it is given."""

    class OtherFake:
        model_id = "other-fake"

        def extract_profile(self, cv_text: str) -> RawProfile:
            return RawProfile(first_name="Pat", target_title="Data Engineer")

    pdf_path = tmp_path / "cv.pdf"
    pdf_path.write_bytes(cv_pdf_bytes("Pat Data Engineer Python"))
    cache = ExtractionCache(tmp_path / "cache")
    profile, from_cache = extract_cv(pdf_path, OtherFake(), cache, "other-fake")
    assert from_cache is False
    assert profile.first_name == "Pat"
    assert profile.target_title == "Data Engineer"


def test_parse_profile_payload_strips_fences() -> None:
    payload = """```json
    {"first_name": "Jane", "target_title": "Backend Engineer"}
    ```"""
    profile = parse_profile_payload(payload)
    assert profile.first_name == "Jane"
    assert profile.target_title == "Backend Engineer"
