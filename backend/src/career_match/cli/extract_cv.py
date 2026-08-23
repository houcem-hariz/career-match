"""Extract a RawProfile from a text PDF. Uses Groq GPT-OSS 20B and a disk cache."""

from __future__ import annotations

from pathlib import Path

import typer

from career_match.adapters.extraction.service import extract_cv
from career_match.adapters.llm.groq_extractor import GroqProfileExtractor
from career_match.adapters.storage.extraction_cache import ExtractionCache
from career_match.settings import get_settings

app = typer.Typer(add_completion=False)


@app.command()
def main(
    pdf_path: Path = typer.Argument(..., exists=True, readable=True, dir_okay=False),
) -> None:
    settings = get_settings()
    extractor = GroqProfileExtractor(settings)
    cache = ExtractionCache(settings.extraction_cache_dir, settings.extraction_cache_enabled)
    profile, from_cache = extract_cv(pdf_path, extractor, cache, settings.llm_chat_model)
    origin = "cache" if from_cache else "llm"
    typer.echo(f"# source={origin}", err=True)
    typer.echo(profile.model_dump_json(indent=2))


if __name__ == "__main__":
    app()
