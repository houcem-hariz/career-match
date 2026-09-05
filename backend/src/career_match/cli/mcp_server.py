"""Start the career-match MCP server over stdio. Do not write to stdout."""

from __future__ import annotations

import sys

from career_match.adapters.mcp.server import create_server
from career_match.pipeline.runtime import build_live_deps, default_data_paths
from career_match.settings import get_settings


def main() -> None:
    settings = get_settings()
    paths = default_data_paths()
    try:
        deps = build_live_deps(
            settings,
            referential_path=paths["referential"],
            scoring_path=paths["scoring"],
            catalogue_path=paths["catalogue"],
        )
    except Exception as exc:
        print(
            "Postgres is unreachable. From the project root run: docker compose up -d",
            file=sys.stderr,
        )
        print(f"({exc.__class__.__name__})", file=sys.stderr)
        raise SystemExit(1) from exc

    print("# career-match MCP server on stdio", file=sys.stderr)
    create_server(deps).run()


if __name__ == "__main__":
    main()
