"""Pipeline nodes. Each wraps an existing week-3 function and returns a state patch."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

from career_match.adapters.extraction.service import extract_cv
from career_match.adapters.indexing.search import search_offers
from career_match.adapters.matching.service import score_retrieved
from career_match.domain.models.profile import Profile, RawProfile
from career_match.domain.normalization.cascade import normalize_profile
from career_match.pipeline.deps import PipelineDeps
from career_match.pipeline.state import MatchState


def extract_node(state: MatchState, deps: PipelineDeps) -> MatchState:
    path = Path(_require(state, "source_path"))
    raw, from_cache = extract_cv(
        path,
        deps.extractor,
        deps.extraction_cache,
        deps.extractor.model_id,
    )
    digest = hashlib.sha256(path.read_bytes()).hexdigest()
    return {
        "raw_profile": raw,
        "extracted_from_cache": from_cache,
        "source_cv_hash": digest,
    }


def load_json_node(state: MatchState, deps: PipelineDeps) -> MatchState:
    """Load a normalised Profile or a RawProfile from JSON. No LLM."""
    del deps
    path = Path(_require(state, "source_path"))
    payload: dict[str, Any] = json.loads(path.read_text(encoding="utf-8"))
    if "profile_id" in payload:
        return {"profile": Profile.model_validate(payload)}
    return {"raw_profile": RawProfile.model_validate(payload)}


def normalize_node(state: MatchState, deps: PipelineDeps) -> MatchState:
    raw = state.get("raw_profile")
    if raw is None:
        raise ValueError("normalize_node requires raw_profile")
    result = normalize_profile(
        raw,
        deps.referential,
        source_cv_hash=state.get("source_cv_hash"),
    )
    return {"profile": result.profile}


def retrieve_node(state: MatchState, deps: PipelineDeps) -> MatchState:
    profile = state.get("profile")
    if profile is None:
        raise ValueError("retrieve_node requires profile")
    k = state.get("k", 10)
    search = search_offers(profile, deps.embedder, deps.embedding_cache, deps.store, k=k)
    return {
        "hits": search.hits,
        "candidate_count": search.candidate_count,
        "query_from_cache": search.query_from_cache,
    }


def score_node(state: MatchState, deps: PipelineDeps) -> MatchState:
    profile = state.get("profile")
    if profile is None:
        raise ValueError("score_node requires profile")
    hits = state.get("hits", ())
    outcome = score_retrieved(
        profile,
        hits,
        deps.offers_by_id,
        deps.catalogue,
        deps.config,
        candidate_count=state.get("candidate_count", len(hits)),
        query_from_cache=state.get("query_from_cache", False),
    )
    return {
        "cards": outcome.cards,
        "candidate_count": outcome.candidate_count,
        "query_from_cache": outcome.query_from_cache,
    }


def _require(state: MatchState, key: str) -> str:
    value = state.get(key)
    if not isinstance(value, str) or not value:
        raise ValueError(f"{key} is required")
    return value
