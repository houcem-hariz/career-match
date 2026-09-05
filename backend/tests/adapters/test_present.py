"""CLI JSON view of a MatchCard. Same payload for match_profile and run_pipeline."""

from pathlib import Path

from career_match.adapters.matching.present import card_payload
from career_match.domain.models.enums import MatchBucket
from career_match.pipeline.nodes import retrieve_node, score_node
from career_match.pipeline.state import MatchState
from tests.pipeline.fakes import deps, senior_backend_profile


def test_card_payload_has_the_oral_fields(tmp_path: Path) -> None:
    pipeline = deps(tmp_path)
    state: MatchState = {"k": 5, "profile": senior_backend_profile()}
    state = {**state, **retrieve_node(state, pipeline)}
    state = {**state, **score_node(state, pipeline)}
    payload = card_payload(state["cards"][0], rank=1)
    assert payload["rank"] == 1
    assert payload["bucket"] == MatchBucket.ELIGIBLE.value
    assert payload["score"] == state["cards"][0].breakdown.total
    assert "dimensions" in payload
    assert "gaps" in payload
    assert "simulations" in payload
    assert payload["source_id"] == "good"
