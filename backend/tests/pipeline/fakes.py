"""Shared fakes for pipeline tests. No Postgres, no live LLM."""

from __future__ import annotations

from pathlib import Path

from career_match.adapters.indexing.service import InMemoryOfferIndex
from career_match.adapters.storage.embedding_cache import EmbeddingCache
from career_match.adapters.storage.extraction_cache import ExtractionCache
from career_match.adapters.storage.offer_index import IndexedOffer
from career_match.domain.models.enums import (
    JobFamily,
    SeniorityLevel,
    SkillLevel,
    SkillRequirement,
)
from career_match.domain.models.offer import Offer
from career_match.domain.models.profile import Profile, RawProfile
from career_match.domain.models.skill import (
    NormalizedSkill,
    RawSkill,
    ReferenceSkill,
    RequiredSkill,
)
from career_match.domain.normalization.cascade import ReferentialIndex
from career_match.domain.scoring.catalog import TrainingCourse
from career_match.domain.scoring.config import DEFAULT_SCORING_CONFIG
from career_match.pipeline.deps import PipelineDeps


class FakeExtractor:
    def __init__(self) -> None:
        self.calls = 0
        self.model_id = "fake-extractor"

    def extract_profile(self, cv_text: str) -> RawProfile:
        self.calls += 1
        return RawProfile(
            first_name="Jane",
            target_title="Senior Backend Engineer",
            target_families=[JobFamily.BACKEND],
            total_years_experience=6,
            skills=[RawSkill(label="Python"), RawSkill(label="K8s")],
        )


class FakeEmbedder:
    model_id = "fake-embed"
    dimensions = 2

    def embed(self, texts: list[str]) -> list[list[float]]:
        return [[1.0, 0.0] for _ in texts]


def referential() -> ReferentialIndex:
    return ReferentialIndex(
        [
            ReferenceSkill(
                skill_id="python",
                canonical_label="Python",
                aliases=("Python",),
                families=(JobFamily.BACKEND,),
                occurrences=66,
            ),
            ReferenceSkill(
                skill_id="kubernetes",
                canonical_label="Kubernetes",
                aliases=("Kubernetes", "K8s"),
                families=(JobFamily.DEVOPS,),
                occurrences=26,
            ),
        ]
    )


def eligible_offer() -> Offer:
    return Offer(
        offer_id="good",
        source_id="good",
        title="Backend",
        family=JobFamily.BACKEND,
        seniority=SeniorityLevel.SENIOR,
        required_skills=[
            RequiredSkill(skill_id="python", requirement=SkillRequirement.MANDATORY),
            RequiredSkill(skill_id="kubernetes", requirement=SkillRequirement.MANDATORY),
        ],
    )


def senior_backend_profile() -> Profile:
    return Profile(
        profile_id="p1",
        target_title="Python backend",
        target_families=[JobFamily.BACKEND],
        seniority=SeniorityLevel.SENIOR,
        skills=[
            NormalizedSkill(skill_id="python", level=SkillLevel.WORKING),
            NormalizedSkill(skill_id="kubernetes", level=SkillLevel.WORKING),
        ],
    )


def deps(tmp_path: Path, offer: Offer | None = None) -> PipelineDeps:
    offer = offer or eligible_offer()
    store = InMemoryOfferIndex()
    store.upsert(
        [
            IndexedOffer(
                source_id=offer.source_id,
                title=offer.title,
                company="Acme",
                description="Python Kubernetes",
                location_text=None,
                family=JobFamily.BACKEND,
                work_model=None,
                embedding=[1.0, 0.0],
                embedding_model="fake-embed",
            )
        ]
    )
    return PipelineDeps(
        extractor=FakeExtractor(),
        extraction_cache=ExtractionCache(tmp_path / "extract"),
        embedder=FakeEmbedder(),
        embedding_cache=EmbeddingCache(tmp_path / "embed"),
        store=store,
        offers_by_id={offer.source_id: offer},
        catalogue=[
            TrainingCourse(
                course_id="k8s-fundamentals",
                title="Kubernetes fundamentals",
                skill_id="kubernetes",
                target_level=SkillLevel.WORKING,
            )
        ],
        config=DEFAULT_SCORING_CONFIG,
        referential=referential(),
    )
