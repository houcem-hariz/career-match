"""POST /api/chat: agent calls session tools, never a live LLM."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from fastapi.testclient import TestClient
from langchain_core.messages import AIMessage, BaseMessage, ToolMessage

from career_match.api.app import create_app
from tests.pipeline.fakes import deps


class ScriptedChatClient:
    def __init__(self, replies: list[AIMessage]) -> None:
        self.replies = list(replies)
        self.messages: list[list[BaseMessage]] = []

    def complete(self, messages: list[BaseMessage], tools: Any) -> AIMessage:
        del tools
        self.messages.append(list(messages))
        if not self.replies:
            return AIMessage(content="(script exhausted)")
        return self.replies.pop(0)


def _app(tmp_path: Path, script: ScriptedChatClient) -> TestClient:
    return TestClient(create_app(deps(tmp_path), chat_client=script))


def test_chat_requires_a_prior_match(tmp_path: Path) -> None:
    script = ScriptedChatClient([AIMessage(content="should not run")])
    client = _app(tmp_path, script)
    response = client.post("/api/chat", json={"message": "Which offer fits me?"})
    assert response.status_code == 404
    assert script.replies  # LLM was not consumed


def test_chat_without_model_is_503(tmp_path: Path) -> None:
    client = TestClient(create_app(deps(tmp_path)))
    client.post("/api/match", json={"text": "Jane Python K8s", "k": 5})
    response = client.post("/api/chat", json={"message": "Why?"})
    assert response.status_code == 503


def test_chat_lists_offers_via_tool_then_replies(tmp_path: Path) -> None:
    script = ScriptedChatClient(
        [
            AIMessage(
                content="",
                tool_calls=[
                    {"name": "list_matched_offers", "args": {}, "id": "1", "type": "tool_call"}
                ],
            ),
            AIMessage(content="Backend at Acme is Eligible."),
        ]
    )
    client = _app(tmp_path, script)
    client.post("/api/match", json={"text": "Jane Python K8s", "k": 5})
    response = client.post("/api/chat", json={"message": "Which offer fits me best?"})
    assert response.status_code == 200
    body = response.json()
    assert body["reply"] == "Backend at Acme is Eligible."
    assert body["tools_used"] == ["list_matched_offers"]

    tool_messages = [m for batch in script.messages for m in batch if isinstance(m, ToolMessage)]
    assert tool_messages
    assert "good" in tool_messages[0].content
    assert "eligible" in tool_messages[0].content


def test_chat_simulates_catalogue_course(tmp_path: Path) -> None:
    script = ScriptedChatClient(
        [
            AIMessage(
                content="",
                tool_calls=[
                    {
                        "name": "simulate_catalogue_course",
                        "args": {"source_id": "good", "course_id": "k8s-fundamentals"},
                        "id": "1",
                        "type": "tool_call",
                    }
                ],
            ),
            AIMessage(content="k8s-fundamentals keeps the offer Eligible."),
        ]
    )
    client = _app(tmp_path, script)
    client.post("/api/match", json={"text": "Jane Python K8s", "k": 5})
    response = client.post(
        "/api/chat",
        json={"message": "Which course helps most?", "source_id": "good"},
    )
    assert response.status_code == 200
    assert response.json()["tools_used"] == ["simulate_catalogue_course"]
    tool_messages = [m for batch in script.messages for m in batch if isinstance(m, ToolMessage)]
    assert "k8s-fundamentals" in tool_messages[0].content
    assert "score_before" in tool_messages[0].content


def test_chat_rejects_blank_message(tmp_path: Path) -> None:
    script = ScriptedChatClient([AIMessage(content="nope")])
    client = _app(tmp_path, script)
    client.post("/api/match", json={"text": "Jane Python K8s", "k": 5})
    response = client.post("/api/chat", json={"message": "   "})
    assert response.status_code == 400
