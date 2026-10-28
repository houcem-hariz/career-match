"""Session chat agent. Explains scored cards; never computes a new score."""

from __future__ import annotations

import json
from collections.abc import Sequence
from dataclasses import dataclass, field
from typing import Any, Protocol

from langchain_core.messages import AIMessage, BaseMessage, HumanMessage, SystemMessage, ToolMessage
from langchain_core.tools import BaseTool, tool

from career_match.adapters.mcp import tools as mcp_tools
from career_match.api.session import GuestSession
from career_match.pipeline.deps import PipelineDeps

_MAX_STEPS = 6

SYSTEM_PROMPT = """You are the career-match assistant.
You explain an already scored matching session. You never invent a score, bucket, gap,
or course impact: those numbers exist only in tool results.
Use tools to read session cards, the stored Profile, or to simulate a catalogue course.
If a tool reports no match, tell the user to run a match first.
Keep answers short. Cite only values that appeared in tool JSON."""


class ChatClient(Protocol):
    def complete(self, messages: list[BaseMessage], tools: Sequence[BaseTool]) -> AIMessage: ...


@dataclass(frozen=True)
class ChatOutcome:
    reply: str
    tools_used: list[str] = field(default_factory=list)


class LangchainChatClient:
    """Thin wrapper so tests can inject a scripted client instead of ChatOpenAI."""

    def __init__(self, llm: Any) -> None:
        self._llm = llm

    def complete(self, messages: list[BaseMessage], tools: Sequence[BaseTool]) -> AIMessage:
        result = self._llm.bind_tools(list(tools)).invoke(messages)
        if isinstance(result, AIMessage):
            return result
        return AIMessage(content=str(result))


def run_session_chat(
    deps: PipelineDeps,
    session: GuestSession,
    *,
    message: str,
    source_id: str | None,
    client: ChatClient,
) -> ChatOutcome:
    toolset = _session_tools(deps, session)
    hint = f"\nThe user is viewing offer source_id={source_id}." if source_id else ""
    messages: list[BaseMessage] = [
        SystemMessage(SYSTEM_PROMPT),
        HumanMessage(message.strip() + hint),
    ]
    used: list[str] = []
    by_name = {item.name: item for item in toolset}

    for _ in range(_MAX_STEPS):
        ai = client.complete(messages, toolset)
        messages.append(ai)
        if not ai.tool_calls:
            text = ai.content if isinstance(ai.content, str) else str(ai.content)
            return ChatOutcome(reply=text.strip() or "I could not form an answer.", tools_used=used)
        for call in ai.tool_calls:
            name = str(call["name"])
            args = call.get("args") or {}
            call_id = str(call["id"])
            used.append(name)
            chosen = by_name.get(name)
            if chosen is None:
                payload = json.dumps({"error": f"unknown tool {name}"})
            else:
                try:
                    raw = chosen.invoke(args)
                    payload = raw if isinstance(raw, str) else json.dumps(raw, default=str)
                except Exception as exc:
                    payload = json.dumps({"error": str(exc)})
            messages.append(ToolMessage(content=payload, tool_call_id=call_id))
    return ChatOutcome(
        reply="I could not finish with the available tools.",
        tools_used=used,
    )


def _session_tools(deps: PipelineDeps, session: GuestSession) -> list[BaseTool]:
    @tool
    def list_matched_offers() -> str:
        """Scored cards in this session: rank, title, bucket, score. Do not invent numbers."""
        if not session.cards:
            return _dump({"error": "No match in this session."})
        return _dump(
            [
                {
                    "source_id": card.source_id,
                    "rank": card.rank,
                    "title": card.title,
                    "company": card.company,
                    "bucket": card.bucket,
                    "score": card.score,
                    "mandatory_gap_count": card.mandatory_gap_count,
                }
                for card in session.cards
            ]
        )

    @tool
    def get_matched_offer(source_id: str) -> str:
        """One scored card (gaps and course simulations) by source_id from this session."""
        for card in session.cards:
            if card.source_id == source_id:
                return _dump(card.model_dump(mode="json"))
        return _dump({"error": f"Unknown offer '{source_id}' in this session."})

    @tool
    def get_session_profile() -> str:
        """The candidate Profile stored in this session."""
        if session.profile is None:
            return _dump({"error": "No profile in this session."})
        return _dump(session.profile.model_dump(mode="json"))

    @tool
    def simulate_catalogue_course(source_id: str, course_id: str) -> str:
        """Re-run simulate_course for a catalogue course. Uses card similarity."""
        card = next((item for item in session.cards if item.source_id == source_id), None)
        if card is None:
            return _dump({"error": f"Unknown offer '{source_id}' in this session."})
        if session.profile is None:
            return _dump({"error": "No profile in this session."})
        try:
            impact = mcp_tools.simulate_course_impact(
                deps,
                session.profile.model_dump(mode="json"),
                source_id,
                course_id,
                card.similarity,
            )
        except ValueError as exc:
            return _dump({"error": str(exc)})
        return _dump(impact)

    return [
        list_matched_offers,
        get_matched_offer,
        get_session_profile,
        simulate_catalogue_course,
    ]


def _dump(payload: object) -> str:
    return json.dumps(payload, ensure_ascii=False, default=str)
