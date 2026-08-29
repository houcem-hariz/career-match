"""Index the 120 curated offers into Postgres + pgvector."""

from __future__ import annotations

from pathlib import Path

import typer

from career_match.adapters.indexing.corpus import documents_from_corpus, load_annotations
from career_match.adapters.indexing.service import index_documents
from career_match.adapters.ingestion.build_referential import load_offers
from career_match.adapters.llm.factory import build_embedder
from career_match.adapters.storage.embedding_cache import EmbeddingCache
from career_match.adapters.storage.offer_index import PostgresOfferIndex
from career_match.settings import get_settings, project_root

app = typer.Typer(add_completion=False)


@app.command()
def main(
    offers_path: Path = typer.Option(
        project_root() / "data" / "raw" / "offers" / "offers.jsonl",
        exists=True,
        readable=True,
    ),
    annotations_path: Path = typer.Option(
        project_root() / "data" / "raw" / "offers" / "source_annotations.json",
        exists=True,
        readable=True,
    ),
) -> None:
    settings = get_settings()
    embedder = build_embedder(settings)
    cache = EmbeddingCache(settings.embedding_cache_dir, settings.extraction_cache_enabled)
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

    offers = load_offers(offers_path)
    annotations = load_annotations(annotations_path)
    documents = documents_from_corpus(offers, annotations)
    stats = index_documents(documents, embedder, cache, store)
    typer.echo(
        f"# indexed={stats.total} embedded={stats.embedded} cached={stats.cached} "
        f"model={embedder.model_id}"
    )
    for family, count in store.counts_by_family().items():
        typer.echo(f"# family {family}={count}")


if __name__ == "__main__":
    app()
