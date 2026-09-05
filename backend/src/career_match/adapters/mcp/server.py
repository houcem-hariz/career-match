"""FastMCP server. Tools are registered here; the bodies live in tools.py."""

from __future__ import annotations

from typing import Any

from mcp.server.fastmcp import FastMCP

from career_match.adapters.mcp import tools
from career_match.pipeline.deps import PipelineDeps

TOOL_NAMES = (
    "extract_profile",
    "normalize_profile",
    "search_offers",
    "match_profile",
    "simulate_course",
)


def create_server(deps: PipelineDeps) -> FastMCP:
    mcp = FastMCP("career-match")

    @mcp.tool()
    def extract_profile(source_path: str) -> dict[str, Any]:
        """Extract a RawProfile from a CV PDF. Uses the extraction cache when possible."""
        return tools.extract_profile(deps, source_path)

    @mcp.tool()
    def normalize_profile(raw_profile: dict[str, Any]) -> dict[str, Any]:
        """Resolve skill labels against the referential. No LLM."""
        return tools.normalize_profile(deps, raw_profile)

    @mcp.tool()
    def search_offers(profile: dict[str, Any], k: int = 10) -> dict[str, Any]:
        """Filter then rank offers by cosine similarity."""
        return tools.search_offers(deps, profile, k=k)

    @mcp.tool()
    def match_profile(source_path: str, k: int = 10) -> dict[str, Any]:
        """Run the LangGraph matching pipeline on a PDF or a profile JSON."""
        return tools.match_profile(deps, source_path, k=k)

    @mcp.tool()
    def simulate_course(
        profile: dict[str, Any],
        source_id: str,
        course_id: str,
        similarity: float,
    ) -> dict[str, Any]:
        """Re-score one offer as if a catalogue course had been completed."""
        return tools.simulate_course_impact(deps, profile, source_id, course_id, similarity)

    return mcp
