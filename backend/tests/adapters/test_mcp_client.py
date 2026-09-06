"""MCP client talks to a fake stdio server. No Postgres, no live LLM."""

from __future__ import annotations

import os
import sys
from pathlib import Path

from mcp.client.stdio import StdioServerParameters

from career_match.adapters.mcp.client import call_mcp_tool_sync, list_mcp_tools_sync
from career_match.adapters.mcp.server import TOOL_NAMES
from career_match.domain.models.enums import MatchBucket
from tests.pipeline.fakes import senior_backend_profile


def _fake_server(tmp_path: Path) -> StdioServerParameters:
    backend = Path(__file__).resolve().parents[2]
    env = {
        "CAREER_MATCH_FAKE_DIR": str(tmp_path),
        "PYTHONPATH": os.pathsep.join([str(backend), str(backend / "src")]),
    }
    return StdioServerParameters(
        command=sys.executable,
        args=["-m", "tests.adapters.mcp_stdio_server"],
        env=env,
        cwd=str(backend),
    )


def test_client_discovers_tools_over_stdio(tmp_path: Path) -> None:
    names = list_mcp_tools_sync(_fake_server(tmp_path))
    assert set(TOOL_NAMES) <= set(names)


def test_client_match_profile_over_stdio(tmp_path: Path) -> None:
    profile_path = tmp_path / "profile.json"
    profile_path.write_text(senior_backend_profile().model_dump_json(), encoding="utf-8")
    payload = call_mcp_tool_sync(
        "match_profile",
        {"source_path": str(profile_path), "k": 5},
        server=_fake_server(tmp_path),
    )
    assert payload["cards"][0]["bucket"] == MatchBucket.ELIGIBLE.value
    assert payload["cards"][0]["source_id"] == "good"
