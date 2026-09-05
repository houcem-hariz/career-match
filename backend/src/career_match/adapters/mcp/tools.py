"""MCP tool bodies. They call pipeline nodes and domain scoring, never invent a score."""

from __future__ import annotations

from typing import Any

from career_match.adapters.matching.present import card_payload, hit_payload
from career_match.domain.models.profile import Profile, RawProfile
from career_match.domain.scoring.simulate import simulate_course
from career_match.pipeline.deps import PipelineDeps
from career_match.pipeline.graph import run_matching
from career_match.pipeline.nodes import extract_node, normalize_node, retrieve_node
from career_match.pipeline.state import MatchState


def extract_profile(deps: PipelineDeps, source_path: str) -> dict[str, Any]:
    patch = extract_node({"source_path": source_path}, deps)
    raw = patch["raw_profile"]
    return {
        "raw_profile": raw.model_dump(mode="json"),
        "extracted_from_cache": patch["extracted_from_cache"],
        "source_cv_hash": patch["source_cv_hash"],
    }


def normalize_profile(deps: PipelineDeps, raw_profile: dict[str, Any]) -> dict[str, Any]:
    state: MatchState = {"raw_profile": RawProfile.model_validate(raw_profile)}
    patch = normalize_node(state, deps)
    return {"profile": patch["profile"].model_dump(mode="json")}


def search_offers(
    deps: PipelineDeps,
    profile: dict[str, Any],
    k: int = 10,
) -> dict[str, Any]:
    state: MatchState = {"profile": Profile.model_validate(profile), "k": k}
    patch = retrieve_node(state, deps)
    hits = patch["hits"]
    return {
        "candidate_count": patch["candidate_count"],
        "query_from_cache": patch["query_from_cache"],
        "hits": [hit_payload(hit, rank) for rank, hit in enumerate(hits, start=1)],
    }


def match_profile(deps: PipelineDeps, source_path: str, k: int = 10) -> dict[str, Any]:
    state = run_matching(deps, source_path, k=k)
    cards = state.get("cards", ())
    return {
        "candidate_count": state.get("candidate_count", len(cards)),
        "query_from_cache": state.get("query_from_cache", False),
        "cards": [card_payload(card, rank) for rank, card in enumerate(cards, start=1)],
    }


def simulate_course_impact(
    deps: PipelineDeps,
    profile: dict[str, Any],
    source_id: str,
    course_id: str,
    similarity: float,
) -> dict[str, Any]:
    offer = deps.offers_by_id.get(source_id)
    if offer is None:
        raise ValueError(f"unknown offer {source_id}")
    course = next((item for item in deps.catalogue if item.course_id == course_id), None)
    if course is None:
        raise ValueError(f"unknown course {course_id}")
    impact = simulate_course(
        Profile.model_validate(profile),
        offer,
        course,
        similarity,
        deps.config,
    )
    return {
        "course_id": impact.course.course_id,
        "title": impact.course.title,
        "skill_id": impact.course.skill_id,
        "score_before": impact.before.total,
        "score_after": impact.after.total,
        "delta": impact.delta,
        "bucket_before": impact.before.bucket.value,
        "bucket_after": impact.after.bucket.value,
    }
