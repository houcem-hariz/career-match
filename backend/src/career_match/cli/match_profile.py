"""End-to-end matching: retrieve, score, bucket, gaps, impact simulation."""

from __future__ import annotations

import json
from pathlib import Path

import typer

from career_match.adapters.indexing.corpus import load_annotations
from career_match.adapters.ingestion.build_referential import load_offers
from career_match.adapters.ingestion.structure_offer import structure_corpus
from career_match.adapters.llm.factory import build_embedder
from career_match.adapters.matching.config_io import load_scoring_config, load_training_catalogue
from career_match.adapters.matching.present import card_payload
from career_match.adapters.matching.profile_loader import load_profile
from career_match.adapters.matching.service import match_profile
from career_match.adapters.storage.embedding_cache import EmbeddingCache
from career_match.adapters.storage.offer_index import PostgresOfferIndex
from career_match.adapters.storage.referential_io import load_referential_index
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
    scoring_path: Path = typer.Option(
        project_root() / "data" / "processed" / "scoring.json",
        exists=True,
        readable=True,
    ),
    catalogue_path: Path = typer.Option(
        project_root() / "data" / "processed" / "training_catalog.json",
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

    index = load_referential_index(referential_path)
    offers_by_id = structure_corpus(
        load_offers(project_root() / "data" / "raw" / "offers" / "offers.jsonl"),
        load_annotations(project_root() / "data" / "raw" / "offers" / "source_annotations.json"),
        index,
    )
    outcome = match_profile(
        profile,
        build_embedder(settings),
        EmbeddingCache(settings.embedding_cache_dir, settings.extraction_cache_enabled),
        store,
        offers_by_id,
        load_training_catalogue(catalogue_path),
        load_scoring_config(scoring_path),
        k=k,
    )
    typer.echo(
        f"# candidates={outcome.candidate_count} returned={len(outcome.cards)} "
        f"query={'cache' if outcome.query_from_cache else 'embedder'} k={k}",
        err=True,
    )
    payload = [card_payload(card, rank) for rank, card in enumerate(outcome.cards, start=1)]
    typer.echo(json.dumps(payload, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    app()
