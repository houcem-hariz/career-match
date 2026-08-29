"""Build data/processed/referentiel.json from the 120-offer corpus."""

from __future__ import annotations

import json
from pathlib import Path

import typer

from career_match.adapters.ingestion.build_referential import (
    collect_mentions,
    load_offers,
    write_referential,
)
from career_match.adapters.llm.factory import build_offer_skill_extractor
from career_match.adapters.storage.extraction_cache import ExtractionCache
from career_match.domain.normalization.referential import build_referential
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
    output_path: Path = typer.Option(project_root() / "data" / "processed" / "referentiel.json"),
) -> None:
    settings = get_settings()
    offers = load_offers(offers_path)
    annotations = json.loads(annotations_path.read_text(encoding="utf-8"))
    extractor = build_offer_skill_extractor(settings)
    cache = ExtractionCache(settings.extraction_cache_dir, settings.extraction_cache_enabled)

    def progress(index: int, total: int, origin: str, title: str) -> None:
        typer.echo(f"[{index}/{total}] {origin}  {title[:80]}", err=True)

    mentions = collect_mentions(
        offers, annotations, extractor, cache, extractor.model_id, on_progress=progress
    )
    skills = build_referential(mentions, min_occurrences=3)
    write_referential(skills, output_path)
    typer.echo(f"Wrote {len(skills)} skills to {output_path}")


if __name__ == "__main__":
    app()
