"""Candidate profile, in its two layers.

``RawProfile`` is what the extraction produced from the CV. ``Profile`` is the normalised
form, the only one the scoring consumes. Keeping both is what allows the human correction
rate to be measured, and it isolates the uncertain step (normalisation) from the
deterministic one (scoring).

Field inclusion rule applied throughout: a field exists only if it feeds the scoring or a
filter. Anything purely descriptive was left out on purpose.
"""

from pydantic import BaseModel, ConfigDict, Field

from career_match.domain.models.enums import (
    ContractType,
    EducationLevel,
    JobFamily,
    LanguageProficiency,
    SeniorityLevel,
    WorkModel,
)
from career_match.domain.models.skill import NormalizedSkill, RawSkill


class Experience(BaseModel):
    """Shared by both layers: its skill labels are explanatory only, never scored.

    ``duration_months`` feeds the seniority derivation, ``family`` feeds the inference of the
    families the candidate is credible in.
    """

    model_config = ConfigDict(frozen=True)

    title: str
    family: JobFamily | None = None
    duration_months: int = Field(ge=0, le=600)
    skill_labels: tuple[str, ...] = ()


class EducationRecord(BaseModel):
    model_config = ConfigDict(frozen=True)

    level: EducationLevel
    field_of_study: str | None = None


class LanguageSkill(BaseModel):
    model_config = ConfigDict(frozen=True)

    language_code: str = Field(min_length=2, max_length=2, description="ISO 639-1")
    proficiency: LanguageProficiency


class WorkPreferences(BaseModel):
    """Consumed as eliminating filters upstream of the scoring, never as a weighted
    dimension: it is both simpler and more honest than turning a location mismatch into a
    few lost points."""

    model_config = ConfigDict(frozen=True)

    locations: tuple[str, ...] = ()
    contract_types: tuple[ContractType, ...] = ()
    work_models: tuple[WorkModel, ...] = ()
    willing_to_relocate: bool = False


class RawProfile(BaseModel):
    """Direct output of the CV extraction. Never scored as is.

    Seniority is deliberately absent: it is derived deterministically from
    ``total_years_experience`` rather than asked from the model, which would invent it.
    """

    first_name: str | None = None
    target_title: str | None = None
    target_families: list[JobFamily] = Field(default_factory=list)
    total_years_experience: float | None = Field(default=None, ge=0, le=60)
    skills: list[RawSkill] = Field(default_factory=list)
    experiences: list[Experience] = Field(default_factory=list)
    education: list[EducationRecord] = Field(default_factory=list)
    languages: list[LanguageSkill] = Field(default_factory=list)
    preferences: WorkPreferences = WorkPreferences()


class Profile(BaseModel):
    """Normalised profile: skills resolved against the referential, seniority derived.

    ``user_edited`` and ``correction_count`` are what make the extraction quality measurable
    without writing a dedicated evaluation harness.
    """

    profile_id: str
    source_cv_hash: str | None = None

    first_name: str | None = None
    target_title: str | None = None
    target_families: list[JobFamily] = Field(default_factory=list)
    total_years_experience: float = Field(default=0.0, ge=0, le=60)
    seniority: SeniorityLevel = SeniorityLevel.JUNIOR

    skills: list[NormalizedSkill] = Field(default_factory=list)
    experiences: list[Experience] = Field(default_factory=list)
    education: list[EducationRecord] = Field(default_factory=list)
    languages: list[LanguageSkill] = Field(default_factory=list)
    preferences: WorkPreferences = WorkPreferences()

    user_edited: bool = False
    correction_count: int = Field(default=0, ge=0)

    def highest_education(self) -> EducationLevel:
        if not self.education:
            return EducationLevel.NONE
        return max(record.level for record in self.education)

    def skill_by_id(self, skill_id: str) -> NormalizedSkill | None:
        return next((skill for skill in self.skills if skill.skill_id == skill_id), None)
