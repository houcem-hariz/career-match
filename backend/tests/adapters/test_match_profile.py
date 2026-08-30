"""Search-then-score pipeline with fakes, no Postgres and no live embeddings."""

from pathlib import Path

from career_match.adapters.indexing.service import InMemoryOfferIndex
from career_match.adapters.matching.service import match_profile
from career_match.adapters.storage.embedding_cache import EmbeddingCache
from career_match.adapters.storage.offer_index import IndexedOffer
from career_match.domain.models.enums import (
    JobFamily,
    MatchBucket,
    SeniorityLevel,
    SkillLevel,
    SkillRequirement,
)
from career_match.domain.models.offer import Offer
from career_match.domain.models.profile import Profile
from career_match.domain.models.skill import NormalizedSkill, RequiredSkill
from career_match.domain.scoring.catalog import TrainingCourse
from career_match.domain.scoring.config import DEFAULT_SCORING_CONFIG


class FakeEmbedder:
    model_id = "fake-embed"
    dimensions = 2

    def embed(self, texts: list[str]) -> list[list[float]]:
        return [[1.0, 0.0] for _ in texts]


def test_match_profile_scores_and_sorts_by_bucket(tmp_path: Path) -> None:
    store = InMemoryOfferIndex()
    store.upsert(
        [
            IndexedOffer(
                source_id="good",
                title="Backend",
                company="Acme",
                description="Python",
                location_text=None,
                family=JobFamily.BACKEND,
                work_model=None,
                embedding=[1.0, 0.0],
                embedding_model="fake-embed",
            )
        ]
    )
    profile = Profile(
        profile_id="p1",
        target_title="Python backend",
        target_families=[JobFamily.BACKEND],
        seniority=SeniorityLevel.SENIOR,
        skills=[
            NormalizedSkill(skill_id="python", level=SkillLevel.WORKING),
            NormalizedSkill(skill_id="kubernetes", level=SkillLevel.WORKING),
        ],
    )
    offer = Offer(
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
    outcome = match_profile(
        profile,
        FakeEmbedder(),
        EmbeddingCache(tmp_path),
        store,
        {"good": offer},
        [],
        DEFAULT_SCORING_CONFIG,
        k=5,
    )
    assert outcome.candidate_count == 1
    assert outcome.cards[0].breakdown.bucket is MatchBucket.ELIGIBLE
    assert outcome.cards[0].breakdown.total > 70


def test_match_attaches_simulation_for_catalogued_gap(tmp_path: Path) -> None:
    store = InMemoryOfferIndex()
    store.upsert(
        [
            IndexedOffer(
                source_id="k8s-role",
                title="Backend",
                company="Acme",
                description="Kubernetes",
                location_text=None,
                family=JobFamily.BACKEND,
                work_model=None,
                embedding=[1.0, 0.0],
                embedding_model="fake-embed",
            )
        ]
    )
    profile = Profile(
        profile_id="p1",
        target_title="Python",
        target_families=[JobFamily.BACKEND],
        seniority=SeniorityLevel.SENIOR,
        skills=[NormalizedSkill(skill_id="python", level=SkillLevel.WORKING)],
    )
    offer = Offer(
        offer_id="k8s-role",
        source_id="k8s-role",
        title="Backend",
        family=JobFamily.BACKEND,
        seniority=SeniorityLevel.SENIOR,
        required_skills=[
            RequiredSkill(skill_id="python", requirement=SkillRequirement.MANDATORY),
            RequiredSkill(skill_id="kubernetes", requirement=SkillRequirement.MANDATORY),
        ],
    )
    catalogue = [
        TrainingCourse(
            course_id="k8s-fundamentals",
            title="Kubernetes fundamentals",
            skill_id="kubernetes",
            target_level=SkillLevel.WORKING,
        )
    ]
    outcome = match_profile(
        profile,
        FakeEmbedder(),
        EmbeddingCache(tmp_path),
        store,
        {"k8s-role": offer},
        catalogue,
        DEFAULT_SCORING_CONFIG,
        k=5,
    )
    assert outcome.cards[0].breakdown.bucket is MatchBucket.REACHABLE
    assert outcome.cards[0].simulations[0].delta > 0
    assert outcome.cards[0].simulations[0].after.bucket is MatchBucket.ELIGIBLE
