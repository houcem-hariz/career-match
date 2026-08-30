"""Hybrid search: filters then cosine similarity against the offer index."""

from __future__ import annotations

import json
from pathlib import Path

import typer

from career_match.adapters.indexing.search import search_offers
from career_match.adapters.llm.factory import build_embedder
from career_match.adapters.matching.profile_loader import load_profile
from career_match.adapters.storage.embedding_cache import EmbeddingCache
from career_match.adapters.storage.offer_index import PostgresOfferIndex
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
    profile = load_profile(source, referential_path)
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


if __name__ == "__main__":
    app()
