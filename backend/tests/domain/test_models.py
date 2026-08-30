"""Schema-level checks.

Cheap on purpose: the point is to have pytest wired from day one and to pin the two
properties the scoring will rely on, namely that the ordinal scales really are ordered and
that the offer exposes its mandatory/preferred split.
"""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from career_match.domain.models import (
    EducationLevel,
    EducationRecord,
    JobFamily,
    LanguageProficiency,
    LanguageSkill,
    Offer,
    Profile,
    RawSkill,
    SeniorityLevel,
    SkillLevel,
    SkillRequirement,
    RequiredSkill,
)


class TestOrdinalScales:
    """The scoring subtracts and compares these values directly, so ordering is load-bearing."""

    def test_skill_levels_are_ordered(self) -> None:
        assert SkillLevel.AWARENESS < SkillLevel.WORKING < SkillLevel.PROFICIENT < SkillLevel.EXPERT

    def test_seniority_gap_is_signed(self) -> None:
        below = SeniorityLevel.JUNIOR - SeniorityLevel.SENIOR
        above = SeniorityLevel.LEAD - SeniorityLevel.MID
        assert below < 0 < above

    def test_education_levels_are_comparable(self) -> None:
        assert EducationLevel.MASTER > EducationLevel.BACHELOR > EducationLevel.NONE

    def test_language_proficiency_follows_cefr_order(self) -> None:
        assert LanguageProficiency.A1 < LanguageProficiency.B2 < LanguageProficiency.C2


class TestProfile:
    def test_highest_education_returns_the_maximum(self) -> None:
        profile = Profile(
            profile_id="p1",
            education=[
                EducationRecord(level=EducationLevel.BACHELOR),
                EducationRecord(level=EducationLevel.MASTER),
                EducationRecord(level=EducationLevel.HIGH_SCHOOL),
            ],
        )
        assert profile.highest_education() is EducationLevel.MASTER

    def test_highest_education_defaults_to_none_when_empty(self) -> None:
        assert Profile(profile_id="p1").highest_education() is EducationLevel.NONE

    def test_skill_lookup_misses_return_none(self) -> None:
        assert Profile(profile_id="p1").skill_by_id("python") is None

    def test_correction_count_cannot_be_negative(self) -> None:
        with pytest.raises(ValidationError):
            Profile(profile_id="p1", correction_count=-1)


class TestOffer:
    @staticmethod
    def _offer() -> Offer:
        return Offer(
            offer_id="o1",
            source_id="src-1",
            title="Backend Engineer",
            family=JobFamily.BACKEND,
            required_skills=[
                RequiredSkill(skill_id="python", requirement=SkillRequirement.MANDATORY),
                RequiredSkill(skill_id="postgresql", requirement=SkillRequirement.MANDATORY),
                RequiredSkill(skill_id="kubernetes", requirement=SkillRequirement.PREFERRED),
            ],
        )

    def test_mandatory_and_preferred_are_split(self) -> None:
        offer = self._offer()
        assert [s.skill_id for s in offer.mandatory_skills()] == ["python", "postgresql"]
        assert [s.skill_id for s in offer.preferred_skills()] == ["kubernetes"]

    def test_required_skill_defaults_to_working_level(self) -> None:
        skill = RequiredSkill(skill_id="go", requirement=SkillRequirement.MANDATORY)
        assert skill.minimum_level is SkillLevel.WORKING


class TestValidation:
    def test_raw_skill_rejects_implausible_experience(self) -> None:
        with pytest.raises(ValidationError):
            RawSkill(label="python", years_experience=99)

    def test_raw_skill_is_immutable(self) -> None:
        skill = RawSkill(label="python")
        with pytest.raises(ValidationError):
            skill.label = "java"  # type: ignore[misc]

    def test_language_code_must_be_iso_639_1(self) -> None:
        with pytest.raises(ValidationError):
            LanguageSkill(language_code="eng", proficiency=LanguageProficiency.C1)
