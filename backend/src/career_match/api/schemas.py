"""Pydantic models that FastAPI exposes in OpenAPI. Same card fields as card_payload."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field


class MatchJsonBody(BaseModel):
    """JSON body. Send exactly one of ``text`` or ``example`` (not a PDF)."""

    model_config = ConfigDict(extra="forbid")

    text: str | None = Field(
        default=None,
        description="Mini-CV paragraph. Same LLM extractor as a PDF, then the graph.",
    )
    example: str | None = Field(
        default=None,
        description="Built-in demo profile id. Currently only jane_doe_backend.",
        examples=["jane_doe_backend"],
    )
    k: int | None = Field(
        default=None,
        ge=1,
        le=120,
        description="Top-k after filters. Overrides the query parameter when set.",
    )


class GapPayload(BaseModel):
    kind: str = Field(description="skill, seniority, or education")
    skill_id: str | None = None
    requirement: str | None = Field(default=None, description="mandatory or preferred")
    have: str | None = None
    need: str | None = None
    detail: str


class SimulationPayload(BaseModel):
    course_id: str
    title: str
    skill_id: str
    score_before: float
    score_after: float
    delta: float
    bucket_before: str
    bucket_after: str


class CardPayload(BaseModel):
    rank: int
    bucket: str = Field(description="eligible, reachable, or out_of_reach")
    score: float = Field(description="Weighted total on 0-100")
    similarity: float = Field(description="Retrieval cosine, also the semantic dimension input")
    source_id: str
    title: str
    company: str | None = None
    family: str
    seniority: str
    work_model: str
    dimensions: dict[str, float] = Field(
        description=(
            "Six axes in 0-1: mandatory_skills, preferred_skills, seniority, "
            "education, languages, semantic"
        )
    )
    mandatory_gap_count: int
    gaps: list[GapPayload]
    simulations: list[SimulationPayload]


class MatchResponse(BaseModel):
    candidate_count: int = Field(description="Offers that passed filters before top-k")
    query_from_cache: bool
    cards: list[CardPayload]


class ErrorBody(BaseModel):
    detail: str
