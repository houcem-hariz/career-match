"""Search then score, bucket, and simulate the week-3 matching chain."""

from __future__ import annotations

from dataclasses import dataclass

from career_match.adapters.embeddings.protocol import Embedder
from career_match.adapters.indexing.search import OfferSearcher, search_offers
from career_match.adapters.storage.embedding_cache import EmbeddingCache
from career_match.domain.models.offer import Offer
from career_match.domain.models.profile import Profile
from career_match.domain.scoring.buckets import BUCKET_RANK
from career_match.domain.scoring.catalog import TrainingCourse
from career_match.domain.scoring.config import ScoringConfig
from career_match.domain.scoring.score import ScoreBreakdown, score_offer
from career_match.domain.scoring.simulate import ImpactSimulation, simulate_mandatory_gaps


@dataclass(frozen=True)
class MatchCard:
    offer: Offer
    similarity: float
    breakdown: ScoreBreakdown
    simulations: tuple[ImpactSimulation, ...]


@dataclass(frozen=True)
class MatchOutcome:
    cards: tuple[MatchCard, ...]
    candidate_count: int
    query_from_cache: bool


def match_profile(
    profile: Profile,
    embedder: Embedder,
    cache: EmbeddingCache,
    store: OfferSearcher,
    offers_by_id: dict[str, Offer],
    catalogue: list[TrainingCourse],
    config: ScoringConfig,
    *,
    k: int = 10,
) -> MatchOutcome:
    search = search_offers(profile, embedder, cache, store, k=k)
    cards: list[MatchCard] = []
    for hit in search.hits:
        offer = offers_by_id.get(hit.source_id)
        if offer is None:
            continue
        breakdown = score_offer(profile, offer, hit.similarity, config)
        simulations = simulate_mandatory_gaps(
            profile,
            offer,
            hit.similarity,
            catalogue,
            config,
            limit=3,
        )
        cards.append(
            MatchCard(
                offer=offer,
                similarity=hit.similarity,
                breakdown=breakdown,
                simulations=simulations,
            )
        )
    cards.sort(key=lambda card: (BUCKET_RANK[card.breakdown.bucket], -card.breakdown.total))
    return MatchOutcome(
        cards=tuple(cards),
        candidate_count=search.candidate_count,
        query_from_cache=search.query_from_cache,
    )
