"""Per-dimension scores in [0, 1]. No I/O."""

from __future__ import annotations

from career_match.domain.models.enums import EducationLevel, SkillLevel
from career_match.domain.models.offer import Offer
from career_match.domain.models.profile import Profile
from career_match.domain.models.skill import RequiredSkill


def clamp01(value: float) -> float:
    return max(0.0, min(1.0, value))


def skill_coverage(profile: Profile, required: list[RequiredSkill]) -> float:
    if not required:
        return 1.0
    return sum(_one_skill(profile, item) for item in required) / len(required)


def _one_skill(profile: Profile, required: RequiredSkill) -> float:
    held = profile.skill_by_id(required.skill_id)
    if held is None:
        return 0.0
    if held.level >= required.minimum_level:
        return 1.0
    return held.level / required.minimum_level


def seniority_score(profile: Profile, offer: Offer) -> float:
    gap = profile.seniority - offer.seniority
    if gap >= 0:
        return 1.0
    if gap == -1:
        return 0.6
    if gap == -2:
        return 0.3
    return 0.0


def education_score(profile: Profile, offer: Offer) -> float:
    if offer.minimum_education is EducationLevel.NONE:
        return 1.0
    have = profile.highest_education()
    if have >= offer.minimum_education:
        return 1.0
    need = int(offer.minimum_education)
    if need <= 0:
        return 1.0
    return clamp01(int(have) / need)


def language_score(profile: Profile, offer: Offer) -> float:
    if not offer.required_languages:
        return 1.0
    by_code = {item.language_code: item.proficiency for item in profile.languages}
    parts: list[float] = []
    for required in offer.required_languages:
        have = by_code.get(required.language_code)
        if have is None:
            parts.append(0.0)
            continue
        if have >= required.minimum_proficiency:
            parts.append(1.0)
            continue
        parts.append(clamp01(int(have) / int(required.minimum_proficiency)))
    return sum(parts) / len(parts)


def semantic_score(similarity: float) -> float:
    return clamp01(similarity)


def is_skill_gap(profile: Profile, required: RequiredSkill) -> bool:
    held = profile.skill_by_id(required.skill_id)
    if held is None:
        return True
    return held.level < required.minimum_level


def held_level(profile: Profile, skill_id: str) -> SkillLevel | None:
    held = profile.skill_by_id(skill_id)
    return None if held is None else held.level
