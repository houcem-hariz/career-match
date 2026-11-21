"""Load gold cases and compare score_offer buckets. No Postgres, no LLM."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

from career_match.adapters.indexing.corpus import load_annotations
from career_match.adapters.ingestion.build_referential import load_offers
from career_match.adapters.ingestion.structure_offer import structure_corpus
from career_match.adapters.matching.config_io import load_scoring_config
from career_match.adapters.storage.referential_io import load_referential_index
from career_match.domain.models.enums import MatchBucket
from career_match.domain.models.offer import Offer
from career_match.domain.models.profile import Profile
from career_match.domain.scoring.config import ScoringConfig
from career_match.domain.scoring.score import score_offer
from career_match.settings import project_root


@dataclass(frozen=True)
class AnnotatedCase:
    case_id: str
    profile_id: str
    source_id: str
    expected_bucket: MatchBucket
    rationale: str


@dataclass(frozen=True)
class CaseResult:
    case: AnnotatedCase
    predicted: MatchBucket
    mandatory_gap_count: int
    seniority_gap: int
    title: str

    @property
    def ok(self) -> bool:
        return self.predicted is self.case.expected_bucket


def eval_dir(root: Path | None = None) -> Path:
    return (root or project_root()) / "data" / "eval"


def load_profiles(directory: Path) -> dict[str, Profile]:
    profiles: dict[str, Profile] = {}
    for path in sorted(directory.glob("*.json")):
        profile = Profile.model_validate_json(path.read_text(encoding="utf-8"))
        profiles[profile.profile_id] = profile
    return profiles


def load_cases(path: Path) -> tuple[list[AnnotatedCase], float]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    similarity = float(payload.get("similarity") or 0.5)
    cases = [
        AnnotatedCase(
            case_id=str(item["id"]),
            profile_id=str(item["profile_id"]),
            source_id=str(item["source_id"]),
            expected_bucket=MatchBucket(item["expected_bucket"]),
            rationale=str(item.get("rationale") or ""),
        )
        for item in payload["cases"]
    ]
    return cases, similarity


def load_corpus_offers(root: Path | None = None) -> dict[str, Offer]:
    base = root or project_root()
    offers = load_offers(base / "data" / "raw" / "offers" / "offers.jsonl")
    annotations = load_annotations(base / "data" / "raw" / "offers" / "source_annotations.json")
    index = load_referential_index(base / "data" / "processed" / "referentiel.json")
    return structure_corpus(offers, annotations, index)


def evaluate_cases(
    *,
    root: Path | None = None,
    config: ScoringConfig | None = None,
) -> list[CaseResult]:
    base = root or project_root()
    folder = eval_dir(base)
    profiles = load_profiles(folder / "profiles")
    cases, similarity = load_cases(folder / "cases.json")
    offers = load_corpus_offers(base)
    policy = config or load_scoring_config(base / "data" / "processed" / "scoring.json")
    results: list[CaseResult] = []
    for case in cases:
        profile = profiles.get(case.profile_id)
        if profile is None:
            raise ValueError(f"Unknown profile_id '{case.profile_id}' in case {case.case_id}.")
        offer = offers.get(case.source_id)
        if offer is None:
            raise ValueError(f"Unknown source_id '{case.source_id}' in case {case.case_id}.")
        breakdown = score_offer(profile, offer, similarity, policy)
        results.append(
            CaseResult(
                case=case,
                predicted=breakdown.bucket,
                mandatory_gap_count=breakdown.mandatory_gap_count,
                seniority_gap=breakdown.seniority_gap,
                title=offer.title,
            )
        )
    return results
