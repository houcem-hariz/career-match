"""Hybrid search with a fake embedder and an in-memory index."""

from pathlib import Path

from career_match.adapters.indexing.search import search_offers
from career_match.adapters.indexing.service import InMemoryOfferIndex
from career_match.adapters.storage.embedding_cache import EmbeddingCache
from career_match.adapters.storage.offer_index import IndexedOffer
from career_match.domain.models.enums import JobFamily, SkillLevel, WorkModel
from career_match.domain.models.profile import Profile, WorkPreferences
from career_match.domain.models.skill import NormalizedSkill
from career_match.domain.retrieval.query import PROFILE_SEARCH_TEXT_VERSION


class FakeEmbedder:
    def __init__(self) -> None:
        self.model_id = "fake-embed"
        self.dimensions = 2
        self.calls = 0

    def embed(self, texts: list[str]) -> list[list[float]]:
        self.calls += 1
        vectors: list[list[float]] = []
        for text in texts:
            lowered = text.lower()
            python_axis = 1.0 if "python" in lowered else 0.0
            react_axis = 1.0 if "react" in lowered else 0.0
            vectors.append([python_axis, react_axis])
        return vectors


def _offer(
    source_id: str, family: JobFamily, embedding: list[float], **kwargs: object
) -> IndexedOffer:
    payload: dict[str, object] = {
        "source_id": source_id,
        "title": source_id,
        "company": "Acme",
        "description": source_id,
        "location_text": None,
        "family": family,
        "work_model": None,
        "embedding": embedding,
        "embedding_model": "fake-embed",
    }
    payload.update(kwargs)
    return IndexedOffer(**payload)  # type: ignore[arg-type]


def test_search_filters_then_ranks_by_similarity(tmp_path: Path) -> None:
    store = InMemoryOfferIndex()
    store.upsert(
        [
            _offer("py-backend", JobFamily.BACKEND, [1.0, 0.0], title="Python API"),
            _offer("react-front", JobFamily.FRONTEND, [0.0, 1.0], title="React SPA"),
            _offer("py-front", JobFamily.FRONTEND, [1.0, 0.0], title="Python frontend"),
        ]
    )
    profile = Profile(
        profile_id="p1",
        target_title="Python backend",
        target_families=[JobFamily.BACKEND],
        skills=[NormalizedSkill(skill_id="python", level=SkillLevel.WORKING)],
    )
    outcome = search_offers(profile, FakeEmbedder(), EmbeddingCache(tmp_path), store, k=5)
    assert outcome.candidate_count == 1
    assert [hit.source_id for hit in outcome.hits] == ["py-backend"]
    assert outcome.hits[0].similarity == 1.0


def test_query_embedding_is_cached(tmp_path: Path) -> None:
    store = InMemoryOfferIndex()
    store.upsert([_offer("py-backend", JobFamily.BACKEND, [1.0, 0.0])])
    profile = Profile(
        profile_id="p1",
        target_title="Python",
        skills=[NormalizedSkill(skill_id="python", level=SkillLevel.WORKING)],
    )
    embedder = FakeEmbedder()
    cache = EmbeddingCache(tmp_path)
    first = search_offers(profile, embedder, cache, store, k=1)
    second = search_offers(profile, embedder, cache, store, k=1)
    assert first.query_from_cache is False
    assert second.query_from_cache is True
    assert embedder.calls == 1
    assert PROFILE_SEARCH_TEXT_VERSION.startswith("profile-")


def test_work_model_filter_keeps_unknown_offers(tmp_path: Path) -> None:
    store = InMemoryOfferIndex()
    store.upsert(
        [
            _offer("remote", JobFamily.BACKEND, [1.0, 0.0], work_model="remote"),
            _offer("unknown", JobFamily.BACKEND, [1.0, 0.0], work_model=None),
            _offer("onsite", JobFamily.BACKEND, [1.0, 0.0], work_model="onsite"),
        ]
    )
    profile = Profile(
        profile_id="p1",
        target_title="Python",
        skills=[NormalizedSkill(skill_id="python", level=SkillLevel.WORKING)],
        preferences=WorkPreferences(work_models=(WorkModel.REMOTE,)),
    )
    outcome = search_offers(profile, FakeEmbedder(), EmbeddingCache(tmp_path), store, k=10)
    assert {hit.source_id for hit in outcome.hits} == {"remote", "unknown"}
