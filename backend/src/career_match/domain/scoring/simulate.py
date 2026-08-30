"""Re-score an offer as if a catalogue course had been completed."""

from __future__ import annotations

from dataclasses import dataclass

from career_match.domain.models.offer import Offer
from career_match.domain.models.profile import Profile
from career_match.domain.scoring.catalog import TrainingCourse, apply_course, course_for_skill
from career_match.domain.scoring.config import DEFAULT_SCORING_CONFIG, ScoringConfig
from career_match.domain.scoring.score import ScoreBreakdown, score_offer


@dataclass(frozen=True)
class ImpactSimulation:
    course: TrainingCourse
    before: ScoreBreakdown
    after: ScoreBreakdown

    @property
    def delta(self) -> float:
        return round(self.after.total - self.before.total, 1)


def simulate_course(
    profile: Profile,
    offer: Offer,
    course: TrainingCourse,
    semantic_similarity: float,
    config: ScoringConfig = DEFAULT_SCORING_CONFIG,
) -> ImpactSimulation:
    before = score_offer(profile, offer, semantic_similarity, config)
    after_profile = apply_course(profile, course)
    after = score_offer(after_profile, offer, semantic_similarity, config)
    return ImpactSimulation(course=course, before=before, after=after)


def simulate_mandatory_gaps(
    profile: Profile,
    offer: Offer,
    semantic_similarity: float,
    catalogue: list[TrainingCourse],
    config: ScoringConfig = DEFAULT_SCORING_CONFIG,
    *,
    limit: int = 3,
) -> tuple[ImpactSimulation, ...]:
    before = score_offer(profile, offer, semantic_similarity, config)
    results: list[ImpactSimulation] = []
    seen: set[str] = set()
    for gap in before.gaps:
        if gap.kind != "skill" or gap.requirement != "mandatory" or gap.skill_id is None:
            continue
        if gap.skill_id in seen:
            continue
        course = course_for_skill(gap.skill_id, catalogue)
        if course is None:
            continue
        seen.add(gap.skill_id)
        simulation = simulate_course(profile, offer, course, semantic_similarity, config)
        if simulation.delta > 0:
            results.append(simulation)
        if len(results) >= limit:
            break
    return tuple(results)
