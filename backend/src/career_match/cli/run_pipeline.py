"""Run the LangGraph matching pipeline from a PDF or a profile JSON."""

from __future__ import annotations

import json
from pathlib import Path

import typer

from career_match.adapters.matching.present import card_payload
from career_match.pipeline.graph import run_matching
from career_match.pipeline.runtime import build_live_deps
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
    try:
        deps = build_live_deps(
            settings,
            referential_path=referential_path,
            scoring_path=scoring_path,
            catalogue_path=catalogue_path,
        )
    except Exception as exc:
        typer.echo(
            "Postgres is unreachable. From the project root run: docker compose up -d",
            err=True,
        )
        typer.echo(f"({exc.__class__.__name__})", err=True)
        raise typer.Exit(code=1) from exc

    state = run_matching(deps, source, k=k)
    cards = state.get("cards", ())
    query = "cache" if state.get("query_from_cache") else "embedder"
    typer.echo(
        f"# candidates={state.get('candidate_count', len(cards))} "
        f"returned={len(cards)} query={query} k={k}",
        err=True,
    )
    payload = [card_payload(card, rank) for rank, card in enumerate(cards, start=1)]
    typer.echo(json.dumps(payload, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    app()
