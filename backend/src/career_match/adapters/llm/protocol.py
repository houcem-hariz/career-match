"""Provider-agnostic extraction contract.

Week 2 will add a second implementation behind the same protocol. The rest of the
pipeline must keep depending on this interface, never on Groq or LangChain directly.
"""

from typing import Protocol

from career_match.domain.models.profile import RawProfile

PROMPT_VERSION = "cv-raw-v1"
OFFER_SKILLS_PROMPT_VERSION = "offer-skills-v1"


class ProfileExtractor(Protocol):
    def extract_profile(self, cv_text: str) -> RawProfile:
        """Fill ``RawProfile`` from plain CV text. Must not invent seniority."""
        ...
