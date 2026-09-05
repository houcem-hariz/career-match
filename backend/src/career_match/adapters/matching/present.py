"""JSON views of match cards and retrieval hits. Shared by CLIs and MCP tools."""

from __future__ import annotations

from career_match.adapters.matching.service import MatchCard
from career_match.domain.retrieval.results import RetrievedOffer


def card_payload(card: MatchCard, rank: int) -> dict[str, object]:
    return {
        "rank": rank,
        "bucket": card.breakdown.bucket.value,
        "score": card.breakdown.total,
        "similarity": card.similarity,
        "source_id": card.offer.source_id,
        "title": card.offer.title,
        "company": card.offer.company,
        "family": card.offer.family.value,
        "seniority": card.offer.seniority.name,
        "work_model": card.offer.work_model.value,
        "dimensions": card.breakdown.dimensions,
        "mandatory_gap_count": card.breakdown.mandatory_gap_count,
        "gaps": [
            {
                "kind": gap.kind,
                "skill_id": gap.skill_id,
                "requirement": gap.requirement,
                "have": gap.have,
                "need": gap.need,
                "detail": gap.detail,
            }
            for gap in card.breakdown.gaps
        ],
        "simulations": [
            {
                "course_id": item.course.course_id,
                "title": item.course.title,
                "skill_id": item.course.skill_id,
                "score_before": item.before.total,
                "score_after": item.after.total,
                "delta": item.delta,
                "bucket_before": item.before.bucket.value,
                "bucket_after": item.after.bucket.value,
            }
            for item in card.simulations
        ],
    }


def hit_payload(hit: RetrievedOffer, rank: int) -> dict[str, object]:
    return {
        "rank": rank,
        "similarity": hit.similarity,
        "source_id": hit.source_id,
        "title": hit.title,
        "company": hit.company,
        "family": hit.family.value,
        "location_text": hit.location_text,
        "work_model": hit.work_model,
    }
