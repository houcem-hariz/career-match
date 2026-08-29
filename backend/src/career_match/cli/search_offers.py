"""Hybrid search: filters then cosine similarity against the offer index."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

import typer

from career_match.adapters.extraction.service import extract_cv
from career_match.adapters.indexing.search import search_offers
from career_match.adapters.llm.factory import build_embedder, build_profile_extractor
from career_match.adapters.storage.embedding_cache import EmbeddingCache
from career_match.adapters.storage.extraction_cache import ExtractionCache
from career_match.adapters.storage.offer_index import PostgresOfferIndex
from career_match.adapters.storage.referential_io import load_referential_index
from career_match.domain.models.profile import Profile, RawProfile
from career_match.domain.normalization.cascade import normalize_profile
from career_match.settings import get_settings, project_root

app = typer.Typer(add_completion=False)


@app.command()
def main(
    source: Path = typer.Argument(..., exists=True, readable=True, dir_okay=False),
    k: int = typer.Option(10, min=1, max=120),
    referential_path: Path = typer.Option(
        project_root() / "data" / "processed" / "referentiel.json",
        exists=True,
        readable=True,
    ),
) -> None:
    settings = get_settings()
    profile = _load_profile(source, referential_path)
    store = PostgresOfferIndex(settings.database_url, settings.embedding_dimensions)
    try:
        store.ensure_schema()
    except Exception as exc:
        typer.echo(
            "Postgres is unreachable. From the project root run: docker compose up -d",
            err=True,
        )
        typer.echo(f"({exc.__class__.__name__})", err=True)
        raise typer.Exit(code=1) from exc

    embedder = build_embedder(settings)
    cache = EmbeddingCache(settings.embedding_cache_dir, settings.extraction_cache_enabled)
    outcome = search_offers(profile, embedder, cache, store, k=k)
    origin = "cache" if outcome.query_from_cache else "embedder"
    typer.echo(
        f"# candidates={outcome.candidate_count} returned={len(outcome.hits)} "
        f"query={origin} k={k}",
        err=True,
    )
    payload = [
        {
            "rank": index,
            "similarity": hit.similarity,
            "source_id": hit.source_id,
            "title": hit.title,
            "company": hit.company,
            "family": hit.family.value,
            "location_text": hit.location_text,
            "work_model": hit.work_model,
        }
        for index, hit in enumerate(outcome.hits, start=1)
    ]
    typer.echo(json.dumps(payload, ensure_ascii=False, indent=2))


def _load_profile(source: Path, referential_path: Path) -> Profile:
    if source.suffix.lower() == ".pdf":
        settings = get_settings()
        extractor = build_profile_extractor(settings)
        cache = ExtractionCache(settings.extraction_cache_dir, settings.extraction_cache_enabled)
        raw, _from_cache = extract_cv(source, extractor, cache, extractor.model_id)
        digest = hashlib.sha256(source.read_bytes()).hexdigest()
        return normalize_profile(
            raw,
            load_referential_index(referential_path),
            source_cv_hash=digest,
        ).profile

    payload: dict[str, Any] = json.loads(source.read_text(encoding="utf-8"))
    if "profile_id" in payload:
        return Profile.model_validate(payload)
    raw = RawProfile.model_validate(payload)
    return normalize_profile(raw, load_referential_index(referential_path)).profile


if __name__ == "__main__":
    app()
