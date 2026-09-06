"""MCP client over stdio. Spawns the server as a separate process."""

from __future__ import annotations

import asyncio
import json
import sys
from typing import Any

from mcp.client.session import ClientSession
from mcp.client.stdio import StdioServerParameters, stdio_client
from mcp.types import CallToolResult


def live_server_parameters() -> StdioServerParameters:
    return StdioServerParameters(
        command=sys.executable,
        args=["-m", "career_match.cli.mcp_server"],
    )


async def list_mcp_tools(server: StdioServerParameters | None = None) -> list[str]:
    params = server or live_server_parameters()
    async with (
        stdio_client(params) as (read, write),
        ClientSession(read, write) as session,
    ):
        await session.initialize()
        listed = await session.list_tools()
        return [tool.name for tool in listed.tools]


async def call_mcp_tool(
    name: str,
    arguments: dict[str, Any] | None = None,
    *,
    server: StdioServerParameters | None = None,
) -> Any:
    params = server or live_server_parameters()
    async with (
        stdio_client(params) as (read, write),
        ClientSession(read, write) as session,
    ):
        await session.initialize()
        result = await session.call_tool(name, arguments or {})
        return unwrap_tool_result(result)


def list_mcp_tools_sync(server: StdioServerParameters | None = None) -> list[str]:
    return asyncio.run(list_mcp_tools(server))


def call_mcp_tool_sync(
    name: str,
    arguments: dict[str, Any] | None = None,
    *,
    server: StdioServerParameters | None = None,
) -> Any:
    return asyncio.run(call_mcp_tool(name, arguments, server=server))


def unwrap_tool_result(result: CallToolResult) -> Any:
    if result.isError:
        texts = [block.text for block in result.content if hasattr(block, "text")]
        raise RuntimeError("MCP tool failed: " + (" ".join(texts) if texts else "unknown error"))
    if result.structuredContent is not None:
        return result.structuredContent
    for block in result.content:
        text = getattr(block, "text", None)
        if not text:
            continue
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            return text
    return None
