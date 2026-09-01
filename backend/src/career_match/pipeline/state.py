"""Shared matching state. Each node reads this bag and returns a partial update."""

from __future__ import annotations

from typing import TypedDict

from career_match.adapters.matching.service import MatchCard
from career_match.domain.models.profile import Profile, RawProfile
from career_match.domain.retrieval.results import RetrievedOffer


class MatchState(TypedDict, total=False):
    """In-process graph state. Domain objects stay objects until MCP needs JSON."""

    source_path: str
    k: int
    raw_profile: RawProfile
    profile: Profile
    source_cv_hash: str
    extracted_from_cache: bool
    hits: tuple[RetrievedOffer, ...]
    cards: tuple[MatchCard, ...]
    candidate_count: int
    query_from_cache: bool
    error: str
