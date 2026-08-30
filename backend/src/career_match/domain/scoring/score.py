"""Compose the six dimension scores, the bucket, and the derived gaps."""

from __future__ import annotations

from dataclasses import dataclass

from career_match.domain.models.enums import MatchBucket, SkillRequirement
from career_match.domain.models.offer import Offer
from career_match.domain.models.profile import Profile
from career_match.domain.scoring.buckets import assign_bucket
from career_match.domain.scoring.config import DEFAULT_SCORING_CONFIG, ScoringConfig
from career_match.domain.scoring.dimensions import (
    education_score,
    is_skill_gap,
    language_score,
    semantic_score,
    seniority_score,
    skill_coverage,
)
from career_match.domain.scoring.gaps import Gap, collect_gaps


@dataclass(frozen=True)
class ScoreBreakdown:
    total: float
    dimensions: dict[str, float]
    bucket: MatchBucket
    seniority_gap: int
    mandatory_gap_count: int
    gaps: tuple[Gap, ...]


def score_offer(
    profile: Profile,
    offer: Offer,
    semantic_similarity: float,
    config: ScoringConfig = DEFAULT_SCORING_CONFIG,
) -> ScoreBreakdown:
    weights = config.weights
    dimensions = {
        "mandatory_skills": skill_coverage(profile, offer.mandatory_skills()),
        "preferred_skills": skill_coverage(profile, offer.preferred_skills()),
        "seniority": seniority_score(profile, offer),
        "education": education_score(profile, offer),
        "languages": language_score(profile, offer),
        "semantic": semantic_score(semantic_similarity),
    }
    total = 100.0 * (
        weights.mandatory_skills * dimensions["mandatory_skills"]
        + weights.preferred_skills * dimensions["preferred_skills"]
        + weights.seniority * dimensions["seniority"]
        + weights.education * dimensions["education"]
        + weights.languages * dimensions["languages"]
        + weights.semantic * dimensions["semantic"]
    )
    mandatory_gap_count = sum(
        1
        for item in offer.required_skills
        if item.requirement is SkillRequirement.MANDATORY and is_skill_gap(profile, item)
    )
    seniority_gap = int(profile.seniority) - int(offer.seniority)
    bucket = assign_bucket(
        mandatory_gap_count=mandatory_gap_count,
        seniority_gap=seniority_gap,
        config=config,
    )
    return ScoreBreakdown(
        total=round(total, 1),
        dimensions={name: round(value, 4) for name, value in dimensions.items()},
        bucket=bucket,
        seniority_gap=seniority_gap,
        mandatory_gap_count=mandatory_gap_count,
        gaps=collect_gaps(profile, offer),
    )
