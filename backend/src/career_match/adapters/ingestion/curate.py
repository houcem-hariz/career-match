"""Select a balanced 120-offer tech subset from the Multi-ATS parquet dump."""

from __future__ import annotations

import hashlib
import json
import re
from collections import defaultdict
from datetime import date, datetime
from pathlib import Path
from typing import Any

import pandas as pd

from career_match.adapters.ingestion.family_hint import infer_family_hint
from career_match.domain.models.enums import JobFamily
from career_match.domain.models.offer import RawOffer

PER_FAMILY = 20
MIN_DESCRIPTION_CHARS = 500
MAX_PER_COMPANY_PER_FAMILY = 2

_ENGLISH_COUNTRIES = {
    "usa",
    "us",
    "united states",
    "united states of america",
    "uk",
    "united kingdom",
    "great britain",
    "canada",
    "ireland",
    "australia",
    "new zealand",
}


def _as_text(value: Any) -> str:
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return ""
    text = str(value).strip()
    if text.lower() in {"nan", "none", "[]"}:
        return ""
    return text


def _join_block(label: str, value: Any) -> str:
    text = _as_text(value)
    if not text:
        return ""
    if text.startswith("[") and text.endswith("]"):
        try:
            items = json.loads(text)
        except json.JSONDecodeError:
            items = None
        if isinstance(items, list):
            bullets = "\n".join(f"- {item}" for item in items if str(item).strip())
            return f"{label}:\n{bullets}" if bullets else ""
    return f"{label}:\n{text}"


def build_description(row: pd.Series) -> str:
    """Rebuild posting-like text without injecting the pre-extracted skill list.

    ``skills_required`` is kept aside as a comparison artefact, not as extractor input.
    """
    parts = [
        _as_text(row.get("job_description")),
        _join_block("Responsibilities", row.get("responsibilities")),
        _join_block("Minimum qualifications", row.get("minimum_qualifications")),
        _join_block("Preferred qualifications", row.get("preferred_qualifications")),
    ]
    return "\n\n".join(part for part in parts if part).strip()


def _location(row: pd.Series) -> str | None:
    city = _as_text(row.get("city"))
    country = _as_text(row.get("country"))
    if city and country:
        return f"{city}, {country}"
    return city or country or None


def _posted_at(value: Any) -> date | None:
    text = _as_text(value)
    if not text:
        return None
    for fmt in ("%Y-%m-%d", "%Y/%m/%d", "%d/%m/%Y"):
        try:
            return datetime.strptime(text[:10], fmt).date()
        except ValueError:
            continue
    return None


def _is_english_enough(row: pd.Series) -> bool:
    country = _as_text(row.get("country")).lower()
    if country in _ENGLISH_COUNTRIES:
        return True
    title = _as_text(row.get("title"))
    non_ascii = len(re.findall(r"[^\x00-\x7F]", title))
    return bool(title) and non_ascii <= 2


def _source_id(title: str, company: str, description: str) -> str:
    payload = f"{title}|{company}|{description[:120]}"
    digest = hashlib.sha1(payload.encode("utf-8")).hexdigest()[:12]
    return f"nextgig-{digest}"


def curate(df: pd.DataFrame) -> tuple[list[RawOffer], dict[str, dict[str, Any]]]:
    """Return the selected offers plus a sidecar of source annotations."""
    buckets: dict[JobFamily, list[tuple[int, RawOffer, dict[str, Any]]]] = defaultdict(list)

    for _idx, row in df.iterrows():
        title = _as_text(row.get("title"))
        skills_blob = _as_text(row.get("skills_required"))
        family = infer_family_hint(title, skills_blob)
        if family is None or not _is_english_enough(row):
            continue

        description = build_description(row)
        if len(description) < MIN_DESCRIPTION_CHARS:
            continue

        company = _as_text(row.get("company_name")) or None
        offer = RawOffer(
            source_id=_source_id(title, company or "", description),
            title=title,
            company=company,
            description=description,
            location_text=_location(row),
            posted_at=_posted_at(row.get("date_posted")),
        )
        annotation = {
            "family_hint": family.value,
            "skills_required": skills_blob,
            "work_model": _as_text(row.get("work_model")) or None,
            "employment_type": _as_text(row.get("employment_type")) or None,
            "experience_level": _as_text(row.get("experience_level")) or None,
        }
        buckets[family].append((len(description), offer, annotation))

    selected: list[RawOffer] = []
    annotations: dict[str, dict[str, Any]] = {}
    seen_keys: set[str] = set()

    for family in JobFamily:
        ranked = sorted(buckets[family], key=lambda item: item[0], reverse=True)
        company_counts: dict[str, int] = defaultdict(int)
        kept = 0
        for _length, offer, annotation in ranked:
            key = f"{offer.title.lower()}|{(offer.company or '').lower()}"
            if key in seen_keys:
                continue
            company_key = (offer.company or "").lower()
            if company_key and company_counts[company_key] >= MAX_PER_COMPANY_PER_FAMILY:
                continue
            seen_keys.add(key)
            company_counts[company_key] += 1
            selected.append(offer)
            annotations[offer.source_id] = annotation
            kept += 1
            if kept >= PER_FAMILY:
                break

    return selected, annotations


def write_corpus(
    offers: list[RawOffer],
    annotations: dict[str, dict[str, Any]],
    output_dir: Path,
) -> Path:
    output_dir.mkdir(parents=True, exist_ok=True)
    corpus_path = output_dir / "offers.jsonl"
    with corpus_path.open("w", encoding="utf-8") as handle:
        for offer in offers:
            handle.write(offer.model_dump_json() + "\n")

    (output_dir / "source_annotations.json").write_text(
        json.dumps(annotations, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )

    counts: dict[str, int] = defaultdict(int)
    for meta in annotations.values():
        counts[str(meta["family_hint"])] += 1
    manifest = {
        "source": "nextgig/global-job-postings-multi-ats-2026-06",
        "license": "CC BY 4.0",
        "count": len(offers),
        "per_family": dict(counts),
        "notes": (
            "job_description in the source is an LLM summary, not the original posting. "
            "We concatenate summary + responsibilities + qualifications. "
            "skills_required is stored in the sidecar for evaluation only."
        ),
    }
    (output_dir / "manifest.json").write_text(
        json.dumps(manifest, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    return corpus_path
