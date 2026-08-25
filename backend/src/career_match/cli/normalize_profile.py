"""Normalize a raw profile (JSON) or a CV PDF against the skill referential."""

from __future__ import annotations

import hashlib
from pathlib import Path

import typer

from career_match.adapters.extraction.service import extract_cv
from career_match.adapters.llm.groq_extractor import GroqProfileExtractor
from career_match.adapters.storage.extraction_cache import ExtractionCache
from career_match.adapters.storage.referential_io import load_referential_index
from career_match.domain.models.profile import RawProfile
from career_match.domain.normalization.cascade import normalize_profile
from career_match.settings import get_settings, project_root

app = typer.Typer(add_completion=False)


@app.command()
def main(
    source: Path = typer.Argument(..., exists=True, readable=True, dir_okay=False),
    referential_path: Path = typer.Option(
        project_root() / "data" / "processed" / "referentiel.json",
        exists=True,
        readable=True,
    ),
) -> None:
    index = load_referential_index(referential_path)
    raw, source_cv_hash = _load_raw(source)
    result = normalize_profile(raw, index, source_cv_hash=source_cv_hash)
    for item in result.unmatched:
        extra = f" (closest: {item.best_candidate} {item.score})" if item.best_candidate else ""
        typer.echo(f"# unmatched [{item.reason}] {item.label}{extra}", err=True)
    typer.echo(f"# matched_skills={len(result.profile.skills)} unmatched={len(result.unmatched)}")
    typer.echo(result.profile.model_dump_json(indent=2))


def _load_raw(source: Path) -> tuple[RawProfile, str | None]:
    if source.suffix.lower() == ".pdf":
        settings = get_settings()
        extractor = GroqProfileExtractor(settings)
        cache = ExtractionCache(settings.extraction_cache_dir, settings.extraction_cache_enabled)
        raw, _from_cache = extract_cv(source, extractor, cache, settings.llm_chat_model)
        digest = hashlib.sha256(source.read_bytes()).hexdigest()
        return raw, digest
    return RawProfile.model_validate_json(source.read_text(encoding="utf-8")), None


if __name__ == "__main__":
    app()
