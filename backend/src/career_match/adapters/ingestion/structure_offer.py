"""Turn a raw corpus item + sidecar into a structured Offer for scoring."""

from __future__ import annotations

from typing import Any

from career_match.adapters.ingestion.build_referential import labels_from_sidecar
from career_match.domain.models.enums import (
    ContractType,
    JobFamily,
    SeniorityLevel,
    SkillRequirement,
    WorkModel,
)
from career_match.domain.models.offer import Offer, RawOffer
from career_match.domain.models.skill import RequiredSkill
from career_match.domain.normalization.cascade import ReferentialIndex, SkillMatch, UnmatchedSkill

MANDATORY_SKILL_CAP = 5

_SENIORITY_LABELS: dict[str, SeniorityLevel] = {
    "intern": SeniorityLevel.JUNIOR,
    "internship": SeniorityLevel.JUNIOR,
    "junior": SeniorityLevel.JUNIOR,
    "entry": SeniorityLevel.JUNIOR,
    "entry level": SeniorityLevel.JUNIOR,
    "mid": SeniorityLevel.MID,
    "mid level": SeniorityLevel.MID,
    "intermediate": SeniorityLevel.MID,
    "associate": SeniorityLevel.MID,
    "senior": SeniorityLevel.SENIOR,
    "sr": SeniorityLevel.SENIOR,
    "staff": SeniorityLevel.LEAD,
    "principal": SeniorityLevel.LEAD,
    "lead": SeniorityLevel.LEAD,
    "distinguished": SeniorityLevel.LEAD,
    "director": SeniorityLevel.LEAD,
}

_TITLE_HINTS: tuple[tuple[str, SeniorityLevel], ...] = (
    ("distinguished", SeniorityLevel.LEAD),
    ("principal", SeniorityLevel.LEAD),
    ("staff", SeniorityLevel.LEAD),
    ("lead", SeniorityLevel.LEAD),
    ("senior", SeniorityLevel.SENIOR),
    ("sr.", SeniorityLevel.SENIOR),
    ("junior", SeniorityLevel.JUNIOR),
    ("intern", SeniorityLevel.JUNIOR),
)

_CONTRACTS: dict[str, ContractType] = {
    "full-time": ContractType.PERMANENT,
    "full time": ContractType.PERMANENT,
    "permanent": ContractType.PERMANENT,
    "contract": ContractType.FIXED_TERM,
    "fixed-term": ContractType.FIXED_TERM,
    "intern": ContractType.INTERNSHIP,
    "internship": ContractType.INTERNSHIP,
    "freelance": ContractType.FREELANCE,
}

_WORK_MODELS: dict[str, WorkModel] = {
    "onsite": WorkModel.ONSITE,
    "on-site": WorkModel.ONSITE,
    "hybrid": WorkModel.HYBRID,
    "remote": WorkModel.REMOTE,
}


def structure_offer(
    raw: RawOffer,
    annotation: dict[str, Any],
    index: ReferentialIndex,
    *,
    family: JobFamily | None = None,
) -> Offer:
    if family is None:
        hint = annotation.get("family_hint")
        if not isinstance(hint, str) or not hint:
            raise ValueError(f"Missing family_hint for offer {raw.source_id}")
        family = JobFamily(hint)
    skills = _required_skills(annotation.get("skills_required"), index)
    work_raw = annotation.get("work_model")
    work_key = work_raw.strip().lower() if isinstance(work_raw, str) else ""
    return Offer(
        offer_id=raw.source_id,
        source_id=raw.source_id,
        title=raw.title,
        company=raw.company,
        family=family,
        seniority=_seniority(annotation.get("experience_level"), raw.title),
        required_skills=skills,
        location=raw.location_text,
        contract_type=_contract(annotation.get("employment_type")),
        work_model=_WORK_MODELS.get(work_key, WorkModel.ONSITE),
        description=raw.description,
    )


def structure_corpus(
    offers: list[RawOffer],
    annotations: dict[str, dict[str, Any]],
    index: ReferentialIndex,
) -> dict[str, Offer]:
    structured: dict[str, Offer] = {}
    for raw in offers:
        structured[raw.source_id] = structure_offer(raw, annotations.get(raw.source_id, {}), index)
    return structured


def _required_skills(raw_sidecar: object, index: ReferentialIndex) -> list[RequiredSkill]:
    labels = labels_from_sidecar(raw_sidecar if isinstance(raw_sidecar, str) else None)
    ranked: list[tuple[int, str]] = []
    seen: set[str] = set()
    for label in labels:
        outcome = index.resolve(label)
        if isinstance(outcome, UnmatchedSkill):
            continue
        assert isinstance(outcome, SkillMatch)
        if outcome.skill_id in seen:
            continue
        seen.add(outcome.skill_id)
        occurrences = index.by_id[outcome.skill_id].occurrences
        ranked.append((occurrences, outcome.skill_id))
    ranked.sort(reverse=True)
    skills: list[RequiredSkill] = []
    for position, (_occurrences, skill_id) in enumerate(ranked):
        if position < MANDATORY_SKILL_CAP:
            requirement = SkillRequirement.MANDATORY
        else:
            requirement = SkillRequirement.PREFERRED
        skills.append(RequiredSkill(skill_id=skill_id, requirement=requirement))
    return skills


def _seniority(raw_level: object, title: str) -> SeniorityLevel:
    if isinstance(raw_level, str) and raw_level.strip():
        key = raw_level.strip().lower().replace("_", " ").replace("-", " ")
        mapped = _SENIORITY_LABELS.get(key)
        if mapped is not None:
            return mapped
    lowered = title.lower()
    for hint, level in _TITLE_HINTS:
        if hint in lowered:
            return level
    return SeniorityLevel.MID


def _contract(raw: object) -> ContractType:
    if not isinstance(raw, str) or not raw.strip():
        return ContractType.PERMANENT
    key = raw.strip().lower().replace("_", " ")
    return _CONTRACTS.get(key, ContractType.PERMANENT)


