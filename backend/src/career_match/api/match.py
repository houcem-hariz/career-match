"""Turn an HTTP match request into a temp source file, then run the graph."""

from __future__ import annotations

from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Any

from career_match.adapters.extraction.service import extract_from_text
from career_match.adapters.matching.present import card_payload
from career_match.adapters.parsing.pdf import EmptyPdfError
from career_match.pipeline.deps import PipelineDeps
from career_match.pipeline.graph import run_matching


class MatchRequestError(ValueError):
    """User input that should map to HTTP 400."""


def match_payload(deps: PipelineDeps, source: Path, *, k: int) -> dict[str, Any]:
    """Same JSON envelope as the MCP match_profile tool."""
    state = run_matching(deps, source, k=k)
    cards = state.get("cards", ())
    return {
        "candidate_count": state.get("candidate_count", len(cards)),
        "query_from_cache": state.get("query_from_cache", False),
        "cards": [card_payload(card, rank) for rank, card in enumerate(cards, start=1)],
    }


def run_match(
    deps: PipelineDeps,
    *,
    k: int = 10,
    pdf_bytes: bytes | None = None,
    text: str | None = None,
    example: str | None = None,
    examples: dict[str, Path] | None = None,
) -> dict[str, Any]:
    k = _require_k(k)
    kind, value = _one_source(pdf_bytes=pdf_bytes, text=text, example=example)
    known = examples or {}

    if kind == "example":
        path = known.get(value)
        if path is None or not path.is_file():
            known_ids = ", ".join(sorted(known)) or "(none)"
            raise MatchRequestError(f"Unknown example '{value}'. Known: {known_ids}.")
        try:
            return match_payload(deps, path, k=k)
        except EmptyPdfError as exc:
            raise MatchRequestError(str(exc)) from exc

    with TemporaryDirectory() as tmp:
        tmp_path = Path(tmp)
        if kind == "pdf":
            source = tmp_path / "cv.pdf"
            source.write_bytes(pdf_bytes or b"")
        else:
            try:
                raw, _ = extract_from_text(
                    value,
                    deps.extractor,
                    deps.extraction_cache,
                    deps.extractor.model_id,
                )
            except ValueError as exc:
                raise MatchRequestError(str(exc)) from exc
            source = tmp_path / "raw.json"
            source.write_text(raw.model_dump_json(), encoding="utf-8")
        try:
            return match_payload(deps, source, k=k)
        except EmptyPdfError as exc:
            raise MatchRequestError(str(exc)) from exc


def _require_k(k: int) -> int:
    if k < 1 or k > 120:
        raise MatchRequestError("k must be between 1 and 120.")
    return k


def _one_source(
    *,
    pdf_bytes: bytes | None,
    text: str | None,
    example: str | None,
) -> tuple[str, str]:
    pdf = pdf_bytes if pdf_bytes else None
    stripped_text = text.strip() if isinstance(text, str) else ""
    stripped_example = example.strip() if isinstance(example, str) else ""
    present = [
        name
        for name, flag in (
            ("pdf", pdf is not None),
            ("text", bool(stripped_text)),
            ("example", bool(stripped_example)),
        )
        if flag
    ]
    if len(present) != 1:
        raise MatchRequestError(
            "Send exactly one of: a PDF (cv), text, or example (jane_doe_backend)."
        )
    if present[0] == "pdf":
        return "pdf", ""
    if present[0] == "text":
        return "text", stripped_text
    return "example", stripped_example
