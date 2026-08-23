"""Assemble the skill referential from the curated offer corpus."""

from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any, Protocol

from career_match.adapters.llm.protocol import OFFER_SKILLS_PROMPT_VERSION
from career_match.adapters.storage.extraction_cache import ExtractionCache
from career_match.domain.models.enums import JobFamily
from career_match.domain.models.offer import RawOffer
from career_match.domain.models.skill import ReferenceSkill


class OfferSkillExtractor(Protocol):
    def extract_skills(self, offer_text: str) -> list[str]: ...


def load_offers(jsonl_path: Path) -> list[RawOffer]:
    offers: list[RawOffer] = []
    for line in jsonl_path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            offers.append(RawOffer.model_validate_json(line))
    return offers


def labels_from_sidecar(raw: str | None) -> list[str]:
    if not raw:
        return []
    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        return [raw.strip()] if raw.strip() else []
    if isinstance(data, list):
        return [str(item).strip() for item in data if str(item).strip()]
    return []


def collect_mentions(
    offers: list[RawOffer],
    annotations: dict[str, dict[str, Any]],
    extractor: OfferSkillExtractor,
    cache: ExtractionCache,
    model: str,
    on_progress: Any | None = None,
) -> list[tuple[str, JobFamily | None]]:
    mentions: list[tuple[str, JobFamily | None]] = []
    total = len(offers)
    for index, offer in enumerate(offers, start=1):
        family = _family_of(annotations.get(offer.source_id))
        source = offer.description.encode("utf-8")
        cache_key = cache.key(source, OFFER_SKILLS_PROMPT_VERSION, model)
        cached = cache.get(cache_key)
        if cached is None:
            skills = _extract_with_retry(extractor, offer.description)
            cache.put(cache_key, {"skills": skills})
            origin = "llm"
        else:
            raw_skills = cached.get("skills", [])
            skills = [str(item) for item in raw_skills] if isinstance(raw_skills, list) else []
            origin = "cache"
        sidecar = labels_from_sidecar(
            str(annotations.get(offer.source_id, {}).get("skills_required") or "")
        )
        for label in [*skills, *sidecar]:
            mentions.append((label, family))
        if on_progress is not None:
            on_progress(index, total, origin, offer.title)
    return mentions


def write_referential(skills: list[ReferenceSkill], output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    payload = [skill.model_dump(mode="json") for skill in skills]
    output_path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")


def _family_of(annotation: dict[str, Any] | None) -> JobFamily | None:
    if not annotation:
        return None
    raw = annotation.get("family_hint")
    if not raw:
        return None
    try:
        return JobFamily(str(raw))
    except ValueError:
        return None


def _extract_with_retry(extractor: OfferSkillExtractor, text: str, attempts: int = 5) -> list[str]:
    delay = 2.0
    for _ in range(attempts):
        try:
            return extractor.extract_skills(text)
        except Exception as error:
            message = str(error).lower()
            if (
                "429" in message
                or "rate limit" in message
                or "json_validate_failed" in message
                or "connection error" in message
                or "timeout" in message
                or "apiconnectionerror" in message
            ):
                time.sleep(delay)
                delay = min(delay * 2, 30)
                continue
            raise
    return []
