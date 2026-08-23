"""Groq implementation of the profile extractor (GPT-OSS 20B)."""

from __future__ import annotations

import json

from langchain_openai import ChatOpenAI

from career_match.domain.models.profile import RawProfile
from career_match.settings import Settings

EXTRACTION_SYSTEM_PROMPT = """You extract a structured candidate profile from a CV.
Reply with a single JSON object that matches the provided schema. No markdown.

Return only fields that appear in the document. Do not invent employers, degrees, or skills.
If a field is unknown, use null or an empty list. Never guess a seniority title.
total_years_experience is the overall professional experience in years, not age.

Skill levels (use these definitions, not a 1-10 scale):
- 1 AWARENESS: exposed to it, cannot work unsupervised
- 2 WORKING: delivers standard tasks unsupervised
- 3 PROFICIENT: handles complex cases, makes design decisions
- 4 EXPERT: reference on the subject, mentors others
If the CV gives no signal, leave level null.

target_families must be a subset of:
backend, frontend, data, devops, cybersecurity, technical_product

education.level is an ordinal:
0 NONE, 1 HIGH_SCHOOL, 2 BACHELOR, 3 MASTER, 4 DOCTORATE

language_code is ISO 639-1 (en, fr, de, es, ...).
proficiency is CEFR: 1=A1, 2=A2, 3=B1, 4=B2, 5=C1, 6=C2.
experience.duration_months is an integer.
preferences stay empty unless the CV states location, contract type, or remote/hybrid/onsite.
"""


def parse_profile_payload(text: str) -> RawProfile:
    """Parse model text into RawProfile, tolerating fences or leading reasoning."""
    stripped = text.strip()
    if stripped.startswith("```"):
        stripped = stripped.strip("`")
        if stripped[:4].lower() == "json":
            stripped = stripped[4:]
        stripped = stripped.strip()
    start = stripped.find("{")
    end = stripped.rfind("}")
    if start == -1 or end == -1 or end <= start:
        raise ValueError("Model output did not contain a JSON object.")
    return RawProfile.model_validate_json(stripped[start : end + 1])


class GroqProfileExtractor:
    def __init__(self, settings: Settings) -> None:
        if not settings.groq_api_key:
            raise ValueError("GROQ_API_KEY is missing. Put it in the project .env file.")
        self._llm = ChatOpenAI(
            model=settings.llm_chat_model,
            api_key=settings.groq_api_key,
            base_url=settings.groq_base_url,
            temperature=0,
        ).bind(response_format={"type": "json_object"})

    def extract_profile(self, cv_text: str) -> RawProfile:
        schema = json.dumps(RawProfile.model_json_schema(), ensure_ascii=False)
        message = self._llm.invoke(
            [
                {
                    "role": "system",
                    "content": EXTRACTION_SYSTEM_PROMPT + "\n\nJSON schema:\n" + schema,
                },
                {"role": "user", "content": cv_text},
            ]
        )
        content = message.content
        if not isinstance(content, str):
            content = str(content)
        return parse_profile_payload(content)


OFFER_SKILLS_PROMPT = """Extract technical skills from this job posting.
Reply with a single JSON object: {"skills": ["Python", "Kubernetes", ...]}.
Include only concrete tools, languages, platforms, frameworks, or methods.
Exclude soft skills, degrees, years of experience, and company names.
Use the wording found in the posting. Empty list if none.
"""


class GroqOfferSkillExtractor:
    def __init__(self, settings: Settings) -> None:
        if not settings.groq_api_key:
            raise ValueError("GROQ_API_KEY is missing. Put it in the project .env file.")
        self._llm = ChatOpenAI(
            model=settings.llm_chat_model,
            api_key=settings.groq_api_key,
            base_url=settings.groq_base_url,
            temperature=0,
        )

    def extract_skills(self, offer_text: str) -> list[str]:
        message = self._llm.invoke(
            [
                {"role": "system", "content": OFFER_SKILLS_PROMPT},
                {"role": "user", "content": offer_text[:4000]},
            ]
        )
        content = message.content
        if not isinstance(content, str):
            content = str(content)
        try:
            payload = _parse_json_object(content)
        except (ValueError, json.JSONDecodeError):
            return []
        skills = payload.get("skills", [])
        if not isinstance(skills, list):
            return []
        return [str(item).strip() for item in skills if str(item).strip()]


def _parse_json_object(text: str) -> dict[str, object]:
    stripped = text.strip()
    if stripped.startswith("```"):
        stripped = stripped.strip("`")
        if stripped[:4].lower() == "json":
            stripped = stripped[4:]
        stripped = stripped.strip()
    start = stripped.find("{")
    end = stripped.rfind("}")
    if start == -1 or end == -1 or end <= start:
        raise ValueError("Model output did not contain a JSON object.")
    loaded: dict[str, object] = json.loads(stripped[start : end + 1])
    return loaded
