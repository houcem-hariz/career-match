"""Gaps derived from the same comparisons as the score. No extra LLM."""

from __future__ import annotations

from dataclasses import dataclass

from career_match.domain.models.enums import EducationLevel, SkillRequirement
from career_match.domain.models.offer import Offer
from career_match.domain.models.profile import Profile
from career_match.domain.scoring.dimensions import held_level, is_skill_gap


@dataclass(frozen=True)
class Gap:
    kind: str
    detail: str
    skill_id: str | None = None
    requirement: str | None = None
    have: str | None = None
    need: str | None = None


def collect_gaps(profile: Profile, offer: Offer) -> tuple[Gap, ...]:
    gaps: list[Gap] = []
    for required in offer.required_skills:
        if not is_skill_gap(profile, required):
            continue
        have = held_level(profile, required.skill_id)
        kind = "mandatory" if required.requirement is SkillRequirement.MANDATORY else "preferred"
        have_label = "missing" if have is None else have.name
        gaps.append(
            Gap(
                kind="skill",
                skill_id=required.skill_id,
                requirement=required.requirement.value,
                have=None if have is None else have.name,
                need=required.minimum_level.name,
                detail=(
                    f"{kind} {required.skill_id}: have {have_label}, "
                    f"need {required.minimum_level.name}"
                ),
            )
        )
    seniority_gap = int(profile.seniority) - int(offer.seniority)
    if seniority_gap < 0:
        gaps.append(
            Gap(
                kind="seniority",
                have=profile.seniority.name,
                need=offer.seniority.name,
                detail=f"seniority {profile.seniority.name} is below {offer.seniority.name}",
            )
        )
    if (
        offer.minimum_education is not EducationLevel.NONE
        and profile.highest_education() < offer.minimum_education
    ):
        gaps.append(
            Gap(
                kind="education",
                have=profile.highest_education().name,
                need=offer.minimum_education.name,
                detail=(
                    f"education {profile.highest_education().name} "
                    f"is below {offer.minimum_education.name}"
                ),
            )
        )
    return tuple(gaps)
