"""Account store and password hashing. No HTTP."""

from __future__ import annotations

from pathlib import Path

import pytest

from career_match.api.accounts import (
    AuthError,
    InMemoryAccountStore,
    JsonAccountStore,
    authenticate,
    hash_password,
    verify_password,
)
from tests.pipeline.fakes import senior_backend_profile


def test_hash_is_salted_and_verifies() -> None:
    digest, salt = hash_password("secret-pass")
    other, other_salt = hash_password("secret-pass")
    assert digest != other
    assert salt != other_salt
    account = InMemoryAccountStore().create("ada@example.com", "secret-pass")
    assert verify_password("secret-pass", account)
    assert not verify_password("wrong-pass", account)


def test_register_normalizes_email_and_rejects_duplicates() -> None:
    store = InMemoryAccountStore()
    first = store.create("Ada@Example.com", "secret-pass")
    assert first.email == "ada@example.com"
    with pytest.raises(AuthError) as exc:
        store.create("ada@example.com", "other-pass")
    assert exc.value.status_code == 409


def test_short_password_and_bad_email() -> None:
    store = InMemoryAccountStore()
    with pytest.raises(AuthError) as exc:
        store.create("ada@example.com", "short")
    assert exc.value.status_code == 400
    with pytest.raises(AuthError) as exc:
        store.create("not-an-email", "secret-pass")
    assert exc.value.status_code == 400


def test_authenticate_rejects_unknown_or_wrong_password() -> None:
    store = InMemoryAccountStore()
    store.create("ada@example.com", "secret-pass")
    with pytest.raises(AuthError) as exc:
        authenticate(store, "ada@example.com", "nope-nope")
    assert exc.value.status_code == 401
    with pytest.raises(AuthError) as exc:
        authenticate(store, "missing@example.com", "secret-pass")
    assert exc.value.status_code == 401


def test_json_store_reloads_profile(tmp_path: Path) -> None:
    path = tmp_path / "accounts.json"
    store = JsonAccountStore(path)
    account = store.create("ada@example.com", "secret-pass")
    account.profile = senior_backend_profile()
    store.put(account)

    reloaded = JsonAccountStore(path)
    found = reloaded.get_by_email("ada@example.com")
    assert found is not None
    assert found.user_id == account.user_id
    assert found.profile is not None
    assert found.profile.profile_id == "p1"
    assert verify_password("secret-pass", found)
