"""Filter the Multi-ATS dump into a 120-offer tech corpus."""

from __future__ import annotations

from pathlib import Path

import pandas as pd
import typer

from career_match.adapters.ingestion.curate import curate, write_corpus

app = typer.Typer(add_completion=False)


@app.command()
def main(
    source: Path = typer.Argument(..., exists=True, readable=True),
    output_dir: Path = typer.Option(
        Path("../data/raw/offers"),
        help="Directory that will receive offers.jsonl and the sidecar files.",
    ),
) -> None:
    df = pd.read_parquet(source) if source.suffix == ".parquet" else pd.read_csv(source)
    offers, annotations = curate(df)
    path = write_corpus(offers, annotations, output_dir)
    counts: dict[str, int] = {}
    for meta in annotations.values():
        family = str(meta["family_hint"])
        counts[family] = counts.get(family, 0) + 1
    typer.echo(f"Wrote {len(offers)} offers to {path}")
    for family, count in sorted(counts.items()):
        typer.echo(f"  {family}: {count}")


if __name__ == "__main__":
    app()
