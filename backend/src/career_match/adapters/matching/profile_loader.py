"""Load a Profile from a PDF, a raw JSON, or an already normalised JSON."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

from career_match.adapters.extraction.service import extract_cv
from career_match.adapters.llm.factory import build_profile_extractor
from career_match.adapters.storage.extraction_cache import ExtractionCache
from career_match.adapters.storage.referential_io import load_referential_index
from career_match.domain.models.profile import Profile, RawProfile
from career_match.domain.normalization.cascade import normalize_profile
from career_match.settings import get_settings


def load_profile(source: Path, referential_path: Path) -> Profile:
    if source.suffix.lower() == ".pdf":
        settings = get_settings()
        extractor = build_profile_extractor(settings)
        cache = ExtractionCache(settings.extraction_cache_dir, settings.extraction_cache_enabled)
        raw, _from_cache = extract_cv(source, extractor, cache, extractor.model_id)
        digest = hashlib.sha256(source.read_bytes()).hexdigest()
        return normalize_profile(
            raw,
            load_referential_index(referential_path),
            source_cv_hash=digest,
        ).profile

    payload: dict[str, Any] = json.loads(source.read_text(encoding="utf-8"))
    if "profile_id" in payload:
        return Profile.model_validate(payload)
    raw = RawProfile.model_validate(payload)
    return normalize_profile(raw, load_referential_index(referential_path)).profile
