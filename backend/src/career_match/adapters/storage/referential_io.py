"""Load the committed skill referential from disk."""

from __future__ import annotations

import json
from pathlib import Path

from career_match.domain.models.skill import ReferenceSkill
from career_match.domain.normalization.cascade import ReferentialIndex


def load_referential(path: Path) -> list[ReferenceSkill]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    return [ReferenceSkill.model_validate(item) for item in payload]


def load_referential_index(path: Path) -> ReferentialIndex:
    return ReferentialIndex(load_referential(path))
