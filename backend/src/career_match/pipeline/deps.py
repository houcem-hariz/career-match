"""Runtime dependencies injected into nodes. Not part of MatchState."""

from __future__ import annotations

from dataclasses import dataclass

from career_match.adapters.embeddings.protocol import Embedder
from career_match.adapters.indexing.search import OfferSearcher
from career_match.adapters.llm.protocol import ProfileExtractor
from career_match.adapters.storage.embedding_cache import EmbeddingCache
from career_match.adapters.storage.extraction_cache import ExtractionCache
from career_match.domain.models.offer import Offer
from career_match.domain.normalization.cascade import ReferentialIndex
from career_match.domain.scoring.catalog import TrainingCourse
from career_match.domain.scoring.config import ScoringConfig


@dataclass(frozen=True)
class PipelineDeps:
    extractor: ProfileExtractor
    extraction_cache: ExtractionCache
    embedder: Embedder
    embedding_cache: EmbeddingCache
    store: OfferSearcher
    offers_by_id: dict[str, Offer]
    catalogue: list[TrainingCourse]
    config: ScoringConfig
    referential: ReferentialIndex
