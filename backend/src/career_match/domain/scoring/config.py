"""Scoring weights and bucket thresholds. Loaded from config, consumed as data."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field, model_validator


class ScoringWeights(BaseModel):
    model_config = ConfigDict(frozen=True)

    mandatory_skills: float = Field(default=0.35, ge=0, le=1)
    preferred_skills: float = Field(default=0.15, ge=0, le=1)
    seniority: float = Field(default=0.15, ge=0, le=1)
    education: float = Field(default=0.10, ge=0, le=1)
    languages: float = Field(default=0.05, ge=0, le=1)
    semantic: float = Field(default=0.20, ge=0, le=1)

    @model_validator(mode="after")
    def weights_sum_to_one(self) -> ScoringWeights:
        total = (
            self.mandatory_skills
            + self.preferred_skills
            + self.seniority
            + self.education
            + self.languages
            + self.semantic
        )
        if abs(total - 1.0) > 1e-6:
            raise ValueError(f"scoring weights must sum to 1.0, got {total}")
        return self


class ScoringConfig(BaseModel):
    """Deterministic matching policy. Changing this file changes every score."""

    model_config = ConfigDict(frozen=True)

    weights: ScoringWeights = ScoringWeights()
    max_mandatory_gaps_reachable: int = Field(default=2, ge=0)
    min_seniority_gap_eligible: int = Field(default=-1)
    min_seniority_gap_reachable: int = Field(default=-2)
    out_of_reach_seniority_gap: int = Field(default=-3)


DEFAULT_SCORING_CONFIG = ScoringConfig()
