"""Load the curated corpus and assemble the text that will be embedded."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from career_match.domain.models.enums import JobFamily
from career_match.domain.models.offer import RawOffer

_WORK_MODEL_ALIASES = {
    "onsite": "onsite",
    "on-site": "onsite",
    "hybrid": "hybrid",
    "remote": "remote",
}


@dataclass(frozen=True)
class OfferDocument:
    source_id: str
    title: str
    company: str | None
    description: str
    location_text: str | None
    family: JobFamily
    work_model: str | None

    def embedding_text(self) -> str:
        return f"{self.title}\n\n{self.description}".strip()


def load_annotations(path: Path) -> dict[str, dict[str, Any]]:
    loaded: dict[str, dict[str, Any]] = json.loads(path.read_text(encoding="utf-8"))
    return loaded


def documents_from_corpus(
    offers: list[RawOffer],
    annotations: dict[str, dict[str, Any]],
) -> list[OfferDocument]:
    documents: list[OfferDocument] = []
    for offer in offers:
        meta = annotations.get(offer.source_id, {})
        raw_family = meta.get("family_hint")
        if not isinstance(raw_family, str) or not raw_family:
            raise ValueError(f"Missing family_hint for offer {offer.source_id}")
        documents.append(
            OfferDocument(
                source_id=offer.source_id,
                title=offer.title,
                company=offer.company,
                description=offer.description,
                location_text=offer.location_text,
                family=JobFamily(raw_family),
                work_model=_work_model(meta.get("work_model")),
            )
        )
    return documents


def _work_model(raw: object) -> str | None:
    if not isinstance(raw, str) or not raw.strip():
        return None
    return _WORK_MODEL_ALIASES.get(raw.strip().lower())
