"""Embedding cache and offer indexing, without calling a live API or Postgres."""

from pathlib import Path

from career_match.adapters.embeddings.protocol import EMBEDDING_TEXT_VERSION
from career_match.adapters.indexing.corpus import OfferDocument, documents_from_corpus
from career_match.adapters.indexing.service import InMemoryOfferIndex, index_documents
from career_match.adapters.storage.embedding_cache import EmbeddingCache
from career_match.domain.models.enums import JobFamily
from career_match.domain.models.offer import RawOffer


class FakeEmbedder:
    def __init__(self) -> None:
        self.model_id = "fake-embed"
        self.dimensions = 4
        self.calls = 0

    def embed(self, texts: list[str]) -> list[list[float]]:
        self.calls += 1
        return [[float(len(text)), 1.0, 0.0, 0.0] for text in texts]


def _document() -> OfferDocument:
    return OfferDocument(
        source_id="o1",
        title="Backend Engineer",
        company="Acme",
        description="Python and PostgreSQL.",
        location_text="Remote, US",
        family=JobFamily.BACKEND,
        work_model="remote",
    )


def test_embedding_text_is_title_then_description() -> None:
    assert _document().embedding_text() == "Backend Engineer\n\nPython and PostgreSQL."


def test_cache_key_changes_with_text_version_and_model(tmp_path: Path) -> None:
    cache = EmbeddingCache(tmp_path)
    text = "same"
    key_a = cache.key(text, "offer-title-desc-v1", "text-embedding-3-small")
    key_b = cache.key(text, "offer-title-desc-v2", "text-embedding-3-small")
    key_c = cache.key(text, "offer-title-desc-v1", "other-model")
    assert len({key_a, key_b, key_c}) == 3


def test_index_uses_cache_on_second_call(tmp_path: Path) -> None:
    cache = EmbeddingCache(tmp_path)
    store = InMemoryOfferIndex()
    embedder = FakeEmbedder()
    docs = [_document()]

    first = index_documents(docs, embedder, cache, store)
    second = index_documents(docs, embedder, cache, store)

    assert first.embedded == 1 and first.cached == 0
    assert second.embedded == 0 and second.cached == 1
    assert embedder.calls == 1
    assert store.count() == 1
    assert store.rows["o1"].family is JobFamily.BACKEND


def test_documents_from_corpus_map_family_and_work_model() -> None:
    offers = [
        RawOffer(
            source_id="nextgig-1",
            title="SRE",
            description="Kubernetes and Terraform.",
            location_text="London, UK",
        )
    ]
    annotations = {
        "nextgig-1": {"family_hint": "devops", "work_model": "On-site"},
    }
    documents = documents_from_corpus(offers, annotations)
    assert documents[0].family is JobFamily.DEVOPS
    assert documents[0].work_model == "onsite"


def test_disabled_cache_always_reembeds(tmp_path: Path) -> None:
    cache = EmbeddingCache(tmp_path, enabled=False)
    store = InMemoryOfferIndex()
    embedder = FakeEmbedder()
    docs = [_document()]
    index_documents(docs, embedder, cache, store)
    index_documents(docs, embedder, cache, store)
    assert embedder.calls == 2
    assert not list(tmp_path.iterdir())
    assert EMBEDDING_TEXT_VERSION.startswith("offer-")
