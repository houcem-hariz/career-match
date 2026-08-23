"""Job offer, mirroring the profile schema.

Same families, same ordinal scales, same skill referential. Without that shared vocabulary
the scoring could not be written cleanly, which is why both schemas were designed as a pair.

``RawOffer`` is the corpus item as downloaded. ``Offer`` is the structured form, produced by
the very same extraction machinery as the CV: one extraction component, two document types.
"""

from datetime import date

from pydantic import BaseModel, ConfigDict, Field

from career_match.domain.models.enums import (
    ContractType,
    EducationLevel,
    JobFamily,
    LanguageProficiency,
    SeniorityLevel,
    SkillRequirement,
    WorkModel,
)
from career_match.domain.models.skill import RequiredSkill


class RequiredLanguage(BaseModel):
    model_config = ConfigDict(frozen=True)

    language_code: str = Field(min_length=2, max_length=2, description="ISO 639-1")
    minimum_proficiency: LanguageProficiency


class RawOffer(BaseModel):
    """Corpus item, kept verbatim. Committed to the repository so that neither development
    nor the demo depends on re-downloading the dataset."""

    source_id: str
    title: str
    company: str | None = None
    description: str
    location_text: str | None = None
    posted_at: date | None = None


class Offer(BaseModel):
    """Structured offer. Every field is consumed either by a filter or by a scoring
    dimension; ``description`` is kept because it carries the semantic similarity."""

    offer_id: str
    source_id: str

    title: str
    company: str | None = None
    family: JobFamily
    seniority: SeniorityLevel = SeniorityLevel.MID

    required_skills: list[RequiredSkill] = Field(default_factory=list)
    minimum_education: EducationLevel = EducationLevel.NONE
    required_languages: list[RequiredLanguage] = Field(default_factory=list)

    location: str | None = None
    contract_type: ContractType = ContractType.PERMANENT
    work_model: WorkModel = WorkModel.ONSITE

    description: str = ""

    def mandatory_skills(self) -> list[RequiredSkill]:
        return [s for s in self.required_skills if s.requirement is SkillRequirement.MANDATORY]

    def preferred_skills(self) -> list[RequiredSkill]:
        return [s for s in self.required_skills if s.requirement is SkillRequirement.PREFERRED]
