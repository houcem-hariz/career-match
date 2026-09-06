"""Call career-match MCP tools from a separate process over stdio."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import typer

from career_match.adapters.mcp.client import call_mcp_tool_sync, list_mcp_tools_sync

app = typer.Typer(add_completion=False)


@app.command("list")
def list_tools() -> None:
    """Ask the server which tools it exposes (dynamic discovery)."""
    names = list_mcp_tools_sync()
    typer.echo(json.dumps(names, ensure_ascii=False, indent=2))


@app.command()
def match(
    source: Path = typer.Argument(..., exists=True, readable=True, dir_okay=False),
    k: int = typer.Option(10, min=1, max=120),
) -> None:
    """Call match_profile on the MCP server."""
    payload = call_mcp_tool_sync(
        "match_profile",
        {"source_path": str(source.resolve()), "k": k},
    )
    typer.echo(json.dumps(payload, ensure_ascii=False, indent=2))


@app.command()
def call(
    tool: str = typer.Argument(..., help="Tool name advertised by the server"),
    arguments: str = typer.Option("{}", help="JSON object of tool arguments"),
) -> None:
    """Call any advertised tool. Used to show that the client does not hard-code one path."""
    parsed: Any = json.loads(arguments)
    if not isinstance(parsed, dict):
        raise typer.BadParameter("arguments must be a JSON object")
    payload = call_mcp_tool_sync(tool, parsed)
    typer.echo(json.dumps(payload, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    app()
