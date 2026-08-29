"""Ranked offer returned by hybrid search, before scoring."""

from dataclasses import dataclass

from career_match.domain.models.enums import JobFamily


@dataclass(frozen=True)
class RetrievedOffer:
    source_id: str
    title: str
    company: str | None
    family: JobFamily
    location_text: str | None
    work_model: str | None
    similarity: float
    description: str
