"""Deterministic skill cascade: exact, then alias, then fuzzy. No LLM, no embeddings."""

from __future__ import annotations

from dataclasses import dataclass
from difflib import SequenceMatcher
from uuid import uuid4

from career_match.domain.models.enums import SeniorityLevel, SkillLevel, SkillSource
from career_match.domain.models.profile import Profile, RawProfile
from career_match.domain.models.skill import NormalizedSkill, RawSkill, ReferenceSkill
from career_match.domain.normalization.referential import skill_id_for, slugify

FUZZY_THRESHOLD = 0.88
DEFAULT_SKILL_LEVEL = SkillLevel.WORKING


@dataclass(frozen=True)
class SkillMatch:
    skill_id: str
    stage: str  # exact | alias | fuzzy


@dataclass(frozen=True)
class UnmatchedSkill:
    label: str
    reason: str  # noise | unknown | ambiguous
    best_candidate: str | None = None
    score: float | None = None


@dataclass(frozen=True)
class NormalizeResult:
    profile: Profile
    unmatched: tuple[UnmatchedSkill, ...]


class ReferentialIndex:
    """Lookup tables over a frozen referential. Built once, queried many times."""

    def __init__(self, skills: list[ReferenceSkill]) -> None:
        self.by_id = {skill.skill_id: skill for skill in skills}
        self._slug_to_id: dict[str, str] = {}
        for skill in skills:
            self._register(skill.skill_id, skill.skill_id)
            self._register(slugify(skill.canonical_label), skill.skill_id)
            for alias in skill.aliases:
                self._register(slugify(alias), skill.skill_id)

    def _register(self, slug: str, skill_id: str) -> None:
        if slug:
            self._slug_to_id.setdefault(slug, skill_id)

    def resolve(self, label: str) -> SkillMatch | UnmatchedSkill:
        mapped = skill_id_for(label)
        if mapped is None:
            return UnmatchedSkill(label=label, reason="noise")

        slug = slugify(label)
        if slug in self._slug_to_id:
            skill_id = self._slug_to_id[slug]
            canonical_slug = slugify(self.by_id[skill_id].canonical_label)
            stage = "exact" if slug in {skill_id, canonical_slug} else "alias"
            return SkillMatch(skill_id=skill_id, stage=stage)

        if mapped in self.by_id:
            return SkillMatch(skill_id=mapped, stage="alias")

        return self._fuzzy(label, slug)

    def _fuzzy(self, label: str, slug: str) -> SkillMatch | UnmatchedSkill:
        scored: list[tuple[float, str]] = []
        seen: set[str] = set()
        for candidate_slug, skill_id in self._slug_to_id.items():
            if skill_id in seen:
                continue
            ratio = SequenceMatcher(None, slug, candidate_slug).ratio()
            if ratio >= FUZZY_THRESHOLD:
                scored.append((ratio, skill_id))
                seen.add(skill_id)
        if not scored:
            best_id, best_ratio = self._best_overall(slug)
            return UnmatchedSkill(
                label=label,
                reason="unknown",
                best_candidate=best_id,
                score=round(best_ratio, 3) if best_id else None,
            )
        scored.sort(key=lambda item: item[0], reverse=True)
        top_ratio, top_id = scored[0]
        tied = [skill_id for ratio, skill_id in scored if ratio == top_ratio]
        if len(tied) > 1:
            return UnmatchedSkill(
                label=label,
                reason="ambiguous",
                best_candidate=top_id,
                score=round(top_ratio, 3),
            )
        return SkillMatch(skill_id=top_id, stage="fuzzy")

    def _best_overall(self, slug: str) -> tuple[str | None, float]:
        best_id: str | None = None
        best_ratio = 0.0
        for skill_id in self.by_id:
            ratio = SequenceMatcher(None, slug, skill_id).ratio()
            if ratio > best_ratio:
                best_ratio = ratio
                best_id = skill_id
        return best_id, best_ratio


def seniority_from_years(years: float) -> SeniorityLevel:
    """Derive seniority from total years. Thresholds are explicit and documented."""
    if years < 2:
        return SeniorityLevel.JUNIOR
    if years < 5:
        return SeniorityLevel.MID
    if years < 10:
        return SeniorityLevel.SENIOR
    return SeniorityLevel.LEAD


def normalize_profile(
    raw: RawProfile,
    index: ReferentialIndex,
    *,
    profile_id: str | None = None,
    source_cv_hash: str | None = None,
) -> NormalizeResult:
    years = raw.total_years_experience or 0.0
    matched: dict[str, NormalizedSkill] = {}
    unmatched: list[UnmatchedSkill] = []

    for raw_skill in raw.skills:
        outcome = index.resolve(raw_skill.label)
        if isinstance(outcome, UnmatchedSkill):
            unmatched.append(outcome)
            continue
        incoming = _to_normalized(outcome.skill_id, raw_skill)
        matched[outcome.skill_id] = _merge_skills(matched.get(outcome.skill_id), incoming)

    profile = Profile(
        profile_id=profile_id or str(uuid4()),
        source_cv_hash=source_cv_hash,
        first_name=raw.first_name,
        target_title=raw.target_title,
        target_families=list(raw.target_families),
        total_years_experience=years,
        seniority=seniority_from_years(years),
        skills=list(matched.values()),
        experiences=list(raw.experiences),
        education=list(raw.education),
        languages=list(raw.languages),
        preferences=raw.preferences,
    )
    return NormalizeResult(profile=profile, unmatched=tuple(unmatched))


def _to_normalized(skill_id: str, raw: RawSkill) -> NormalizedSkill:
    return NormalizedSkill(
        skill_id=skill_id,
        level=raw.level if raw.level is not None else DEFAULT_SKILL_LEVEL,
        years_experience=raw.years_experience,
        source=SkillSource.CV_EXTRACTION,
    )


def _max_years(left: float | None, right: float | None) -> float | None:
    if left is None:
        return right
    if right is None:
        return left
    return max(left, right)


def _merge_skills(existing: NormalizedSkill | None, incoming: NormalizedSkill) -> NormalizedSkill:
    if existing is None:
        return incoming
    return NormalizedSkill(
        skill_id=incoming.skill_id,
        level=max(existing.level, incoming.level),
        years_experience=_max_years(existing.years_experience, incoming.years_experience),
        source=incoming.source,
    )
