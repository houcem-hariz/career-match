"""Closed training catalogue and impact simulation."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict

from career_match.domain.models.enums import SkillLevel, SkillSource
from career_match.domain.models.profile import Profile
from career_match.domain.models.skill import NormalizedSkill


class TrainingCourse(BaseModel):
    model_config = ConfigDict(frozen=True)

    course_id: str
    title: str
    skill_id: str
    target_level: SkillLevel = SkillLevel.WORKING


def apply_course(profile: Profile, course: TrainingCourse) -> Profile:
    """Return a copy of the profile as if the course had been completed."""
    updated: list[NormalizedSkill] = []
    found = False
    for skill in profile.skills:
        if skill.skill_id != course.skill_id:
            updated.append(skill)
            continue
        found = True
        new_level = skill.level if skill.level >= course.target_level else course.target_level
        updated.append(
            NormalizedSkill(
                skill_id=skill.skill_id,
                level=new_level,
                years_experience=skill.years_experience,
                source=SkillSource.INFERRED,
            )
        )
    if not found:
        updated.append(
            NormalizedSkill(
                skill_id=course.skill_id,
                level=course.target_level,
                source=SkillSource.INFERRED,
            )
        )
    return profile.model_copy(update={"skills": updated})


def course_for_skill(skill_id: str, catalogue: list[TrainingCourse]) -> TrainingCourse | None:
    return next((course for course in catalogue if course.skill_id == skill_id), None)
