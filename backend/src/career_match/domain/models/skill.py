"""Skill representations across the three places a skill can live.

- ``RawSkill``        as written in the source document, before any normalisation
- ``NormalizedSkill`` resolved against the referential, the only form the scoring consumes
- ``RequiredSkill``   the offer side, with its mandatory/preferred flag
- ``ReferenceSkill``  an entry of the referential itself
"""

from pydantic import BaseModel, ConfigDict, Field

from career_match.domain.models.enums import (
    JobFamily,
    SkillLevel,
    SkillRequirement,
    SkillSource,
)


class RawSkill(BaseModel):
    """Skill exactly as the extraction produced it. Never used for scoring."""

    model_config = ConfigDict(frozen=True)

    label: str = Field(description="Verbatim wording found in the source document")
    level: SkillLevel | None = Field(
        default=None, description="Left empty when the document gives no usable signal"
    )
    years_experience: float | None = Field(default=None, ge=0, le=50)


class NormalizedSkill(BaseModel):
    """Skill resolved against the referential. This is what the scoring reads."""

    model_config = ConfigDict(frozen=True)

    skill_id: str
    level: SkillLevel
    years_experience: float | None = Field(default=None, ge=0, le=50)
    source: SkillSource = SkillSource.CV_EXTRACTION


class RequiredSkill(BaseModel):
    """Skill expected by an offer."""

    model_config = ConfigDict(frozen=True)

    skill_id: str
    requirement: SkillRequirement
    minimum_level: SkillLevel = SkillLevel.WORKING


class ReferenceSkill(BaseModel):
    """One entry of the skill referential, derived from the offer corpus.

    ``aliases`` carries the surface forms met in the corpus (``ReactJS``, ``React.js``) and
    feeds the deterministic stage of the normalisation cascade.
    """

    model_config = ConfigDict(frozen=True)

    skill_id: str
    canonical_label: str
    aliases: tuple[str, ...] = ()
    families: tuple[JobFamily, ...] = ()
    occurrences: int = Field(
        default=0, ge=0, description="Number of corpus offers mentioning this skill"
    )
