"""Cosine similarity helpers for in-memory ranking."""

from __future__ import annotations

import math

from career_match.adapters.storage.offer_index import IndexedOffer
from career_match.domain.retrieval.results import RetrievedOffer


def cosine_similarity(left: list[float], right: list[float]) -> float:
    if not left or not right or len(left) != len(right):
        return 0.0
    dot = sum(a * b for a, b in zip(left, right, strict=True))
    norm_left = math.sqrt(sum(a * a for a in left))
    norm_right = math.sqrt(sum(b * b for b in right))
    if norm_left == 0.0 or norm_right == 0.0:
        return 0.0
    return dot / (norm_left * norm_right)


def to_retrieved(row: IndexedOffer, similarity: float) -> RetrievedOffer:
    return RetrievedOffer(
        source_id=row.source_id,
        title=row.title,
        company=row.company,
        family=row.family,
        location_text=row.location_text,
        work_model=row.work_model,
        similarity=round(similarity, 4),
        description=row.description,
    )
