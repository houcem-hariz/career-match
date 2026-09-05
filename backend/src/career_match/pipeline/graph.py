"""Compiled LangGraph matching workflow. Nodes stay thin; this file only wires edges."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from langgraph.graph import END, START, StateGraph

from career_match.pipeline.deps import PipelineDeps
from career_match.pipeline.nodes import (
    extract_node,
    load_json_node,
    normalize_node,
    retrieve_node,
    score_node,
)
from career_match.pipeline.state import MatchState


def build_matching_graph(deps: PipelineDeps) -> Any:
    """Linear retrieve→score, with one ingest branch: PDF vs JSON."""

    def extract(state: MatchState) -> MatchState:
        return extract_node(state, deps)

    def load_json(state: MatchState) -> MatchState:
        return load_json_node(state, deps)

    def normalize(state: MatchState) -> MatchState:
        return normalize_node(state, deps)

    def retrieve(state: MatchState) -> MatchState:
        return retrieve_node(state, deps)

    def score(state: MatchState) -> MatchState:
        return score_node(state, deps)

    graph = StateGraph(MatchState)
    graph.add_node("extract", extract)
    graph.add_node("load_json", load_json)
    graph.add_node("normalize", normalize)
    graph.add_node("retrieve", retrieve)
    graph.add_node("score", score)
    graph.add_conditional_edges(
        START,
        route_from_source,
        {"extract": "extract", "load_json": "load_json"},
    )
    graph.add_edge("extract", "normalize")
    graph.add_conditional_edges(
        "load_json",
        route_after_json,
        {"normalize": "normalize", "retrieve": "retrieve"},
    )
    graph.add_edge("normalize", "retrieve")
    graph.add_edge("retrieve", "score")
    graph.add_edge("score", END)
    return graph.compile()


def run_matching(
    deps: PipelineDeps,
    source_path: str | Path,
    *,
    k: int = 10,
) -> MatchState:
    graph = build_matching_graph(deps)
    result = graph.invoke({"source_path": str(source_path), "k": k})
    return result  # type: ignore[no-any-return]


def route_from_source(state: MatchState) -> str:
    path = state.get("source_path", "")
    if Path(path).suffix.lower() == ".pdf":
        return "extract"
    return "load_json"


def route_after_json(state: MatchState) -> str:
    if state.get("profile") is not None:
        return "retrieve"
    return "normalize"
