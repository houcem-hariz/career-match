"""Embed offer documents and upsert them into the vector index."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from career_match.adapters.embeddings.protocol import EMBEDDING_TEXT_VERSION, Embedder
from career_match.adapters.indexing.corpus import OfferDocument
from career_match.adapters.indexing.similarity import cosine_similarity, to_retrieved
from career_match.adapters.storage.embedding_cache import EmbeddingCache
from career_match.adapters.storage.offer_index import IndexedOffer
from career_match.domain.retrieval.filters import RetrievalFilters, passes_filters
from career_match.domain.retrieval.results import RetrievedOffer


class OfferStore(Protocol):
    def upsert(self, rows: list[IndexedOffer]) -> None: ...


@dataclass(frozen=True)
class IndexStats:
    total: int
    embedded: int
    cached: int


class InMemoryOfferIndex:
    def __init__(self) -> None:
        self.rows: dict[str, IndexedOffer] = {}

    def upsert(self, rows: list[IndexedOffer]) -> None:
        for row in rows:
            self.rows[row.source_id] = row

    def count(self) -> int:
        return len(self.rows)

    def search(
        self,
        query: list[float],
        filters: RetrievalFilters,
        k: int,
    ) -> tuple[tuple[RetrievedOffer, ...], int]:
        passed = [
            row
            for row in self.rows.values()
            if passes_filters(
                family=row.family,
                location_text=row.location_text,
                work_model=row.work_model,
                filters=filters,
            )
        ]
        ranked = sorted(
            passed,
            key=lambda row: cosine_similarity(query, row.embedding),
            reverse=True,
        )
        hits = tuple(
            to_retrieved(row, cosine_similarity(query, row.embedding))
            for row in ranked[: max(k, 0)]
        )
        return hits, len(passed)


def index_documents(
    documents: list[OfferDocument],
    embedder: Embedder,
    cache: EmbeddingCache,
    store: OfferStore,
) -> IndexStats:
    vectors: dict[str, list[float]] = {}
    pending: list[OfferDocument] = []
    cached = 0

    for document in documents:
        cache_key = cache.key(document.embedding_text(), EMBEDDING_TEXT_VERSION, embedder.model_id)
        hit = cache.get(cache_key)
        if hit is not None:
            vectors[document.source_id] = hit
            cached += 1
        else:
            pending.append(document)

    if pending:
        embedded = embedder.embed([item.embedding_text() for item in pending])
        if len(embedded) != len(pending):
            raise ValueError("Embedder returned a different number of vectors than inputs.")
        for document, vector in zip(pending, embedded, strict=True):
            cache.put(
                cache.key(document.embedding_text(), EMBEDDING_TEXT_VERSION, embedder.model_id),
                vector,
            )
            vectors[document.source_id] = vector

    rows = [
        IndexedOffer(
            source_id=document.source_id,
            title=document.title,
            company=document.company,
            description=document.description,
            location_text=document.location_text,
            family=document.family,
            work_model=document.work_model,
            embedding=vectors[document.source_id],
            embedding_model=embedder.model_id,
        )
        for document in documents
    ]
    store.upsert(rows)
    return IndexStats(total=len(documents), embedded=len(pending), cached=cached)
