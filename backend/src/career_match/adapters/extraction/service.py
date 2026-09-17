"""Orchestrate PDF to cache to LLM to RawProfile."""

from __future__ import annotations

from pathlib import Path

from career_match.adapters.llm.protocol import PROMPT_VERSION, ProfileExtractor
from career_match.adapters.parsing.pdf import extract_text
from career_match.adapters.storage.extraction_cache import ExtractionCache
from career_match.domain.models.profile import RawProfile


def extract_cv(
    pdf_path: Path,
    extractor: ProfileExtractor,
    cache: ExtractionCache,
    model: str,
) -> tuple[RawProfile, bool]:
    """Return the profile and whether it was served from cache."""
    source = pdf_path.read_bytes()
    cache_key = cache.key(source, PROMPT_VERSION, model)
    cached = cache.get(cache_key)
    if cached is not None:
        return RawProfile.model_validate(cached), True

    text = extract_text(source)
    profile = extractor.extract_profile(text)
    cache.put(cache_key, profile.model_dump(mode="json"))
    return profile, False


def extract_from_text(
    text: str,
    extractor: ProfileExtractor,
    cache: ExtractionCache,
    model: str,
) -> tuple[RawProfile, bool]:
    """Same extractor and cache as a PDF, without parsing a file."""
    stripped = text.strip()
    if not stripped:
        raise ValueError("Empty text: nothing to extract.")
    source = stripped.encode("utf-8")
    cache_key = cache.key(source, PROMPT_VERSION, model)
    cached = cache.get(cache_key)
    if cached is not None:
        return RawProfile.model_validate(cached), True

    profile = extractor.extract_profile(stripped)
    cache.put(cache_key, profile.model_dump(mode="json"))
    return profile, False
