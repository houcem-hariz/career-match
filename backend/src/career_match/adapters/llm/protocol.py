"""Provider-agnostic extraction contract.

The CLI and later the LangGraph pipeline depend on this interface and on
``build_profile_extractor``, never on Groq or OpenAI classes directly.
"""

from typing import Protocol

from career_match.domain.models.profile import RawProfile

PROMPT_VERSION = "cv-raw-v1"
OFFER_SKILLS_PROMPT_VERSION = "offer-skills-v1"


class ProfileExtractor(Protocol):
    model_id: str

    def extract_profile(self, cv_text: str) -> RawProfile:
        """Fill ``RawProfile`` from plain CV text. Must not invent seniority."""
        ...


class OfferSkillExtractor(Protocol):
    model_id: str

    def extract_skills(self, offer_text: str) -> list[str]:
        """Return technical skill labels found in a job posting."""
        ...
