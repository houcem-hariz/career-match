"""Stdio MCP server with in-memory fakes. Spawned by client tests only."""

from __future__ import annotations

import os
from pathlib import Path

from career_match.adapters.mcp.server import create_server
from tests.pipeline.fakes import deps


def main() -> None:
    tmp = Path(os.environ["CAREER_MATCH_FAKE_DIR"])
    create_server(deps(tmp)).run()


if __name__ == "__main__":
    main()
