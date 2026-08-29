"""Hybrid search: embed the profile, filter, then rank by cosine similarity."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from career_match.adapters.embeddings.protocol import Embedder
from career_match.adapters.storage.embedding_cache import EmbeddingCache
from career_match.domain.models.profile import Profile
from career_match.domain.retrieval.filters import RetrievalFilters
from career_match.domain.retrieval.query import PROFILE_SEARCH_TEXT_VERSION, profile_search_text
from career_match.domain.retrieval.results import RetrievedOffer


class OfferSearcher(Protocol):
    def search(
        self,
        query: list[float],
        filters: RetrievalFilters,
        k: int,
    ) -> tuple[tuple[RetrievedOffer, ...], int]: ...


@dataclass(frozen=True)
class SearchOutcome:
    hits: tuple[RetrievedOffer, ...]
    candidate_count: int
    query_from_cache: bool


def search_offers(
    profile: Profile,
    embedder: Embedder,
    cache: EmbeddingCache,
    store: OfferSearcher,
    *,
    k: int = 10,
) -> SearchOutcome:
    filters = RetrievalFilters.from_profile(profile)
    text = profile_search_text(profile)
    cache_key = cache.key(text, PROFILE_SEARCH_TEXT_VERSION, embedder.model_id)
    cached = cache.get(cache_key)
    if cached is None:
        vectors = embedder.embed([text])
        if len(vectors) != 1:
            raise ValueError("Embedder must return one vector for the profile query.")
        query = vectors[0]
        cache.put(cache_key, query)
        from_cache = False
    else:
        query = cached
        from_cache = True
    hits, candidate_count = store.search(query, filters, k)
    return SearchOutcome(hits=hits, candidate_count=candidate_count, query_from_cache=from_cache)
