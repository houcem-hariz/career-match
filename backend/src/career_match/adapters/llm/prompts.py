"""Shared extraction prompt and JSON parsing. Provider-agnostic."""

from __future__ import annotations

import json

from career_match.domain.models.profile import RawProfile

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

OFFER_SKILLS_PROMPT = """Extract technical skills from this job posting.
Reply with a single JSON object: {"skills": ["Python", "Kubernetes", ...]}.
Include only concrete tools, languages, platforms, frameworks, or methods.
Exclude soft skills, degrees, years of experience, and company names.
Use the wording found in the posting. Empty list if none.
"""


def parse_profile_payload(text: str) -> RawProfile:
    """Parse model text into RawProfile, tolerating fences or leading reasoning."""
    return RawProfile.model_validate_json(_extract_json_object(text))


def parse_skill_list_payload(text: str) -> list[str]:
    try:
        payload = json.loads(_extract_json_object(text))
    except (ValueError, json.JSONDecodeError):
        return []
    skills = payload.get("skills", [])
    if not isinstance(skills, list):
        return []
    return [str(item).strip() for item in skills if str(item).strip()]


def _extract_json_object(text: str) -> str:
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
    return stripped[start : end + 1]
