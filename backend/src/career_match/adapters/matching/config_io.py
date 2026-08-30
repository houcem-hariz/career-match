"""Load scoring policy and the closed training catalogue from disk."""

from __future__ import annotations

import json
from pathlib import Path

from career_match.domain.scoring.catalog import TrainingCourse
from career_match.domain.scoring.config import ScoringConfig


def load_scoring_config(path: Path) -> ScoringConfig:
    payload = json.loads(path.read_text(encoding="utf-8"))
    return ScoringConfig.model_validate(payload)


def load_training_catalogue(path: Path) -> list[TrainingCourse]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, list):
        raise ValueError("training catalogue must be a JSON list")
    return [TrainingCourse.model_validate(item) for item in payload]
