"""In-memory accounts. Password hashes stay here; never in API responses."""

from __future__ import annotations

import hashlib
import json
import secrets
from dataclasses import dataclass, field
from pathlib import Path
from typing import Protocol

from career_match.api.schemas import CardPayload
from career_match.domain.models.profile import Profile

_PBKDF2_ROUNDS = 120_000


class AuthError(ValueError):
    """Auth failure. ``status_code`` is 400, 401, or 409."""

    def __init__(self, message: str, status_code: int = 401) -> None:
        super().__init__(message)
        self.status_code = status_code


@dataclass
class Account:
    user_id: str
    email: str
    password_hash: str
    salt: str
    profile: Profile | None = None
    candidate_count: int = 0
    query_from_cache: bool = False
    cards: list[CardPayload] = field(default_factory=list)

    def to_json(self) -> dict[str, object]:
        return {
            "user_id": self.user_id,
            "email": self.email,
            "password_hash": self.password_hash,
            "salt": self.salt,
            "profile": self.profile.model_dump(mode="json") if self.profile else None,
            "candidate_count": self.candidate_count,
            "query_from_cache": self.query_from_cache,
            "cards": [card.model_dump(mode="json") for card in self.cards],
        }

    @classmethod
    def from_json(cls, payload: dict[str, object]) -> Account:
        raw_profile = payload.get("profile")
        raw_cards = payload.get("cards")
        cards = raw_cards if isinstance(raw_cards, list) else []
        return cls(
            user_id=str(payload["user_id"]),
            email=str(payload["email"]),
            password_hash=str(payload["password_hash"]),
            salt=str(payload["salt"]),
            profile=Profile.model_validate(raw_profile) if raw_profile else None,
            candidate_count=_as_int(payload.get("candidate_count")),
            query_from_cache=bool(payload.get("query_from_cache")),
            cards=[CardPayload.model_validate(card) for card in cards],
        )


class AccountStore(Protocol):
    def get_by_email(self, email: str) -> Account | None: ...

    def get_by_id(self, user_id: str) -> Account | None: ...

    def create(self, email: str, password: str) -> Account: ...

    def put(self, account: Account) -> None: ...


class InMemoryAccountStore:
    def __init__(self) -> None:
        self._by_email: dict[str, Account] = {}
        self._by_id: dict[str, Account] = {}

    def get_by_email(self, email: str) -> Account | None:
        return self._by_email.get(_normalize_email(email))

    def get_by_id(self, user_id: str) -> Account | None:
        return self._by_id.get(user_id)

    def create(self, email: str, password: str) -> Account:
        normalized = _normalize_email(email)
        _require_password(password)
        if normalized in self._by_email:
            raise AuthError("Email already registered.", 409)
        password_hash, salt = hash_password(password)
        account = Account(
            user_id=secrets.token_urlsafe(12),
            email=normalized,
            password_hash=password_hash,
            salt=salt,
        )
        self.put(account)
        return account

    def put(self, account: Account) -> None:
        self._by_email[account.email] = account
        self._by_id[account.user_id] = account


class JsonAccountStore(InMemoryAccountStore):
    """Same as memory, flushed to a gitignored JSON file so a reboot keeps accounts."""

    def __init__(self, path: Path) -> None:
        super().__init__()
        self.path = path
        self._load()

    def put(self, account: Account) -> None:
        super().put(account)
        self._flush()

    def _load(self) -> None:
        if not self.path.is_file():
            return
        raw = json.loads(self.path.read_text(encoding="utf-8"))
        for item in raw.get("accounts", []):
            account = Account.from_json(item)
            self._by_email[account.email] = account
            self._by_id[account.user_id] = account

    def _flush(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        payload = {"accounts": [account.to_json() for account in self._by_id.values()]}
        self.path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def hash_password(password: str, salt: bytes | None = None) -> tuple[str, str]:
    raw_salt = salt or secrets.token_bytes(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), raw_salt, _PBKDF2_ROUNDS)
    return digest.hex(), raw_salt.hex()


def verify_password(password: str, account: Account) -> bool:
    digest, _ = hash_password(password, bytes.fromhex(account.salt))
    return secrets.compare_digest(digest, account.password_hash)


def authenticate(store: AccountStore, email: str, password: str) -> Account:
    account = store.get_by_email(email)
    if account is None or not verify_password(password, account):
        raise AuthError("Invalid email or password.", 401)
    return account


def _normalize_email(email: str) -> str:
    value = email.strip().lower()
    if "@" not in value or value.startswith("@") or value.endswith("@"):
        raise AuthError("Invalid email.", 400)
    return value


def _require_password(password: str) -> None:
    if len(password) < 8:
        raise AuthError("Password must be at least 8 characters.", 400)


def _as_int(value: object) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        return 0
    return value
