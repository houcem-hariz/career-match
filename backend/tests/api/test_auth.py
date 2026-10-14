"""Try-then-save auth: guest match first, account only persists the Profile."""

from __future__ import annotations

from pathlib import Path

from fastapi.testclient import TestClient

from career_match.api.accounts import InMemoryAccountStore
from career_match.api.app import create_app
from career_match.api.session import COOKIE_NAME, SessionStore
from tests.pipeline.fakes import deps


def test_guest_can_match_without_account(tmp_path: Path) -> None:
    client = TestClient(create_app(deps(tmp_path)))
    matched = client.post("/api/match", json={"text": "Jane Python K8s", "k": 5})
    assert matched.status_code == 200
    me = client.get("/api/auth/me")
    assert me.status_code == 200
    assert me.json() == {"authenticated": False, "email": None}


def test_register_attaches_guest_profile(tmp_path: Path) -> None:
    client = TestClient(create_app(deps(tmp_path)))
    client.post("/api/match", json={"text": "Jane Python K8s", "k": 5})
    profile = client.get("/api/profile").json()

    created = client.post(
        "/api/auth/register",
        json={"email": "Ada@Example.com", "password": "secret-pass"},
    )
    assert created.status_code == 201
    assert created.json() == {"authenticated": True, "email": "ada@example.com"}
    assert client.get("/api/auth/me").json()["authenticated"] is True
    assert client.get("/api/profile").json()["profile_id"] == profile["profile_id"]


def test_register_duplicate_is_409(tmp_path: Path) -> None:
    client = TestClient(create_app(deps(tmp_path)))
    body = {"email": "ada@example.com", "password": "secret-pass"}
    assert client.post("/api/auth/register", json=body).status_code == 201
    again = client.post("/api/auth/register", json=body)
    assert again.status_code == 409


def test_login_rejects_bad_password(tmp_path: Path) -> None:
    client = TestClient(create_app(deps(tmp_path)))
    client.post("/api/auth/register", json={"email": "ada@example.com", "password": "secret-pass"})
    client.post("/api/auth/logout")
    response = client.post(
        "/api/auth/login",
        json={"email": "ada@example.com", "password": "wrong-password"},
    )
    assert response.status_code == 401


def test_login_hydrates_when_guest_has_no_profile(tmp_path: Path) -> None:
    accounts = InMemoryAccountStore()
    app = create_app(deps(tmp_path), accounts=accounts)
    first = TestClient(app)
    first.post("/api/match", json={"text": "Jane Python K8s", "k": 5})
    cards = first.get("/api/offers").json()["cards"]
    first.post("/api/auth/register", json={"email": "ada@example.com", "password": "secret-pass"})

    second = TestClient(create_app(deps(tmp_path), accounts=accounts, store=SessionStore()))
    logged = second.post(
        "/api/auth/login",
        json={"email": "ada@example.com", "password": "secret-pass"},
    )
    assert logged.status_code == 200
    assert COOKIE_NAME in second.cookies
    assert second.get("/api/profile").status_code == 200
    assert second.get("/api/offers").json()["cards"] == cards


def test_in_memory_profile_wins_on_login(tmp_path: Path) -> None:
    accounts = InMemoryAccountStore()
    first = TestClient(create_app(deps(tmp_path), accounts=accounts))
    first.post("/api/match", json={"text": "Jane Python K8s", "k": 5})
    first.post("/api/auth/register", json={"email": "ada@example.com", "password": "secret-pass"})
    saved_id = first.get("/api/profile").json()["profile_id"]
    first.post("/api/auth/logout")

    guest = TestClient(create_app(deps(tmp_path), accounts=accounts))
    guest.post("/api/match", json={"text": "Other Python K8s", "k": 5})
    guest_id = guest.get("/api/profile").json()["profile_id"]
    assert guest_id != saved_id
    guest.post("/api/auth/login", json={"email": "ada@example.com", "password": "secret-pass"})
    assert guest.get("/api/profile").json()["profile_id"] == guest_id

    later = TestClient(create_app(deps(tmp_path), accounts=accounts, store=SessionStore()))
    later.post("/api/auth/login", json={"email": "ada@example.com", "password": "secret-pass"})
    assert later.get("/api/profile").json()["profile_id"] == guest_id


def test_logout_keeps_cards_and_clears_auth(tmp_path: Path) -> None:
    client = TestClient(create_app(deps(tmp_path)))
    client.post("/api/match", json={"text": "Jane Python K8s", "k": 5})
    client.post("/api/auth/register", json={"email": "ada@example.com", "password": "secret-pass"})
    logged_out = client.post("/api/auth/logout")
    assert logged_out.status_code == 204
    assert client.get("/api/auth/me").json()["authenticated"] is False
    assert client.get("/api/offers").status_code == 200
    assert client.get("/api/profile").status_code == 200


def test_register_without_match_leaves_offers_empty(tmp_path: Path) -> None:
    client = TestClient(create_app(deps(tmp_path)))
    assert client.post(
        "/api/auth/register",
        json={"email": "ada@example.com", "password": "secret-pass"},
    ).status_code == 201
    assert client.get("/api/offers").status_code == 404
    assert client.get("/api/profile").status_code == 404
