"""In-memory guest session. Cookie only; no accounts yet."""

from __future__ import annotations

import secrets
from dataclasses import dataclass

from career_match.api.schemas import CardPayload, MatchResponse
from career_match.domain.models.profile import Profile

COOKIE_NAME = "cm_session"


class NotFoundError(ValueError):
    """Missing session or unknown offer. Maps to HTTP 404."""


@dataclass
class GuestSession:
    candidate_count: int
    query_from_cache: bool
    cards: list[CardPayload]
    profile: Profile | None = None

    def to_match_response(self) -> MatchResponse:
        return MatchResponse(
            candidate_count=self.candidate_count,
            query_from_cache=self.query_from_cache,
            cards=self.cards,
        )

    def card(self, source_id: str) -> CardPayload:
        for item in self.cards:
            if item.source_id == source_id:
                return item
        raise NotFoundError(f"Unknown offer '{source_id}' in this session.")


class SessionStore:
    def __init__(self) -> None:
        self._sessions: dict[str, GuestSession] = {}

    def new_id(self) -> str:
        return secrets.token_urlsafe(16)

    def get(self, session_id: str | None) -> GuestSession | None:
        if not session_id:
            return None
        return self._sessions.get(session_id)

    def require(self, session_id: str | None) -> GuestSession:
        session = self.get(session_id)
        if session is None:
            raise NotFoundError("No match in this session. POST /api/match first.")
        return session

    def put(self, session_id: str, session: GuestSession) -> None:
        self._sessions[session_id] = session
