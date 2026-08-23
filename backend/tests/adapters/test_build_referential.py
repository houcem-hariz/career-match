"""Referential assembly from offers, with a fake extractor."""

from __future__ import annotations

import json
from pathlib import Path

from career_match.adapters.ingestion.build_referential import (
    collect_mentions,
    labels_from_sidecar,
)
from career_match.adapters.storage.extraction_cache import ExtractionCache
from career_match.domain.models.enums import JobFamily
from career_match.domain.models.offer import RawOffer


class FakeSkillExtractor:
    def extract_skills(self, offer_text: str) -> list[str]:
        return ["React.js"] if "React" in offer_text else ["Python"]


def test_labels_from_sidecar_parses_json_list() -> None:
    assert labels_from_sidecar('["React", "Node.js"]') == ["React", "Node.js"]
    assert labels_from_sidecar("") == []


def test_collect_mentions_unions_llm_and_sidecar_and_caches(tmp_path: Path) -> None:
    offer = RawOffer(
        source_id="o1",
        title="Frontend Engineer",
        description="We need React developers.",
    )
    annotations = {
        "o1": {"family_hint": "frontend", "skills_required": '["TypeScript"]'},
    }
    cache = ExtractionCache(tmp_path)
    extractor = FakeSkillExtractor()
    first = collect_mentions([offer], annotations, extractor, cache, "model")
    second = collect_mentions([offer], annotations, extractor, cache, "model")
    labels = [label for label, _family in first]
    assert "React.js" in labels
    assert "TypeScript" in labels
    assert all(family is JobFamily.FRONTEND for _label, family in first)
    assert first == second
    cached = json.loads(next(tmp_path.glob("*.json")).read_text(encoding="utf-8"))
    assert cached["skills"] == ["React.js"]
