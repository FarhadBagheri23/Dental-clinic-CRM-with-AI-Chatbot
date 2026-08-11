"""Auth checks.

The load-bearing one is test_verifies_seeder_hash: the hashes in Mongo were
written by seeder/seed.py, and if this backend cannot verify them every
existing account is locked out.
"""

import hashlib
import secrets
import time
from datetime import datetime

import jwt
import pytest
from fastapi.testclient import TestClient

from app.core.config import settings
from app.db.mongodb import get_db
from app.api.deps import SESSION_COOKIE
from app.main import app
from app.core.security import DUMMY_HASH, create_token, read_token, verify_password

PASSWORD = "CorrectHorse!1405"


def seeder_hash(password: str) -> str:
    """Copy of seeder/seed.py:hash_password — the format we must stay compatible with."""
    salt = secrets.token_bytes(16)
    dk = hashlib.scrypt(
        password.encode(), salt=salt, n=16384, r=8, p=1, dklen=64,
        maxmem=64 * 1024 * 1024,
    )
    return f"scrypt$16384$8$1${salt.hex()}${dk.hex()}"


# ----------------------------------------------------------------- hashing

def test_verifies_seeder_hash():
    stored = seeder_hash(PASSWORD)
    assert verify_password(PASSWORD, stored)
    assert not verify_password(PASSWORD + "x", stored)


@pytest.mark.parametrize("stored", [
    "", "notahash", "bcrypt$1$2$3$4$5", "scrypt$16384$8$1$zz$zz",
    "scrypt$16384$8$1$00", None, 12345,
])
def test_malformed_hashes_are_rejected_not_raised(stored):
    assert verify_password(PASSWORD, stored) is False


def test_dummy_hash_never_matches():
    assert not verify_password(PASSWORD, DUMMY_HASH)
    assert not verify_password("", DUMMY_HASH)


# ------------------------------------------------------------------ tokens

def test_token_round_trip():
    claims = read_token(create_token(
        {"username": "admin", "display_name": "مدیر سیستم", "role": "مدیر"}
    ))
    assert claims["sub"] == "admin"
    assert claims["name"] == "مدیر سیستم"
    assert claims["role"] == "مدیر"


def test_expired_token_is_rejected():
    stale = jwt.encode(
        {"sub": "admin", "exp": int(time.time()) - 1},
        settings.session_secret, algorithm="HS256",
    )
    assert read_token(stale) is None


def test_token_signed_with_another_secret_is_rejected():
    forged = jwt.encode({"sub": "admin", "exp": int(time.time()) + 60},
                        "another-secret", algorithm="HS256")
    assert read_token(forged) is None


def test_missing_token_is_rejected():
    assert read_token(None) is None
    assert read_token("") is None


# --------------------------------------------------------------- endpoints

class FakeUsers:
    def __init__(self, doc):
        self._doc = doc

    async def find_one(self, query):
        return self._doc if query["username"] == self._doc["username"] else None


class FakeCollection:
    """Enough of a Mongo collection for the login throttle: docs keyed by `key`.

    Only the operators throttle.py actually issues are implemented — $inc and
    $set with upsert. A fuller fake would be inventing behaviour nothing calls.
    """

    def __init__(self):
        self.docs = {}

    async def find_one(self, query):
        doc = self.docs.get(query["key"])
        if doc is None:
            return None
        # Mongo stores datetimes as UTC and hands them back *naive*. Copying
        # that here is the whole point of the fake: with tz-aware values the
        # throttle passed its tests while never engaging on a UTC+03:30 host,
        # because a naive UTC value is read as local time.
        return {
            k: (v.replace(tzinfo=None) if isinstance(v, datetime) else v)
            for k, v in doc.items()
        }

    async def update_one(self, query, update, upsert=False):
        key = query["key"]
        doc = self.docs.get(key) or {"key": key, "failures": 0}
        doc["failures"] = doc["failures"] + update.get("$inc", {}).get("failures", 0)
        doc.update(update.get("$set", {}))
        self.docs[key] = doc

    async def delete_one(self, query):
        self.docs.pop(query["key"], None)

    async def create_index(self, *args, **kwargs):
        return None


class FakeDB:
    def __init__(self, doc):
        self.users = FakeUsers(doc)
        self._collections = {}

    def __getitem__(self, name):
        return self._collections.setdefault(name, FakeCollection())


@pytest.fixture
def client():
    doc = {
        "username": "admin",
        "password_hash": seeder_hash(PASSWORD),
        "display_name": "مدیر سیستم",
        "role": "مدیر",
    }
    # One instance for the whole test, not one per request: the throttle keeps
    # its counters in the database, so a fresh fake per call would reset them
    # and quietly make every lockout assertion pass for the wrong reason.
    db = FakeDB(doc)
    app.dependency_overrides[get_db] = lambda: db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


def test_login_sets_httponly_cookie_and_me_reads_it(client):
    r = client.post("/api/auth/login", json={"username": "admin", "password": PASSWORD})
    assert r.status_code == 200, r.text
    assert r.json() == {"username": "admin", "name": "مدیر سیستم", "role": "مدیر"}
    assert "httponly" in r.headers["set-cookie"].lower()

    assert client.get("/api/auth/me").json()["username"] == "admin"


def test_wrong_password_and_unknown_user_are_indistinguishable(client):
    wrong = client.post("/api/auth/login", json={"username": "admin", "password": "nope"})
    unknown = client.post("/api/auth/login", json={"username": "ghost", "password": "nope"})
    assert wrong.status_code == unknown.status_code == 401
    assert wrong.json() == unknown.json()
    assert SESSION_COOKIE not in wrong.cookies


def test_me_requires_a_session(client):
    assert client.get("/api/auth/me").status_code == 401


# ------------------------------------------- English-only credential rules

@pytest.mark.parametrize("username", [
    "ادمین",           # Persian letters
    "admin۱",          # Persian digit U+06F1 — looks like "admin1"
    "ad min",          # space
    "admin@clinic",    # '@' not in the allowed set
])
def test_non_english_username_is_rejected(client, username):
    r = client.post("/api/auth/login",
                    json={"username": username, "password": PASSWORD})
    assert r.status_code == 422
    assert "انگلیسی" in r.text


@pytest.mark.parametrize("password", [
    "رمزعبور",              # Persian letters
    "Correct۱405",         # Persian digit hiding in an otherwise ASCII password
    "has space",           # space
])
def test_non_english_password_is_rejected(client, password):
    r = client.post("/api/auth/login",
                    json={"username": "admin", "password": password})
    assert r.status_code == 422
    assert "انگلیسی" in r.text


def test_persian_digit_is_not_treated_as_its_ascii_lookalike(client):
    """U+06F1 renders as '۱' and is visually confusable with '1'. It must not
    silently pass as the ASCII digit."""
    assert "۱" != "1"
    r = client.post("/api/auth/login",
                    json={"username": "admin", "password": "CorrectHorse!۱405"})
    assert r.status_code == 422


def test_ascii_symbols_are_still_allowed_in_passwords(client):
    """The rule bans non-English, not punctuation — don't weaken passwords.

    Stays under MAX_FAILURES so the throttle does not turn these into 429s;
    what is being asserted is that they reach auth at all.
    """
    for pw in ["p@ssw0rd!", "~`{}|:<>?"]:
        r = client.post("/api/auth/login", json={"username": "admin", "password": pw})
        assert r.status_code == 401, f"{pw!r} should reach auth, not be rejected as invalid"


# ------------------------------------------------------ brute-force throttle

def test_repeated_failures_lock_the_account_out(client):
    """Unlimited guesses against one account was the whole panel.

    scrypt's ~100ms is not a brake: it runs in a threadpool, so attempts do
    not even serialise.
    """
    from app.core.throttle import MAX_FAILURES

    for attempt in range(MAX_FAILURES):
        r = client.post("/api/auth/login", json={"username": "admin", "password": "wrong"})
        assert r.status_code == 401, f"attempt {attempt} should still be answered"

    blocked = client.post("/api/auth/login", json={"username": "admin", "password": "wrong"})
    assert blocked.status_code == 429
    assert int(blocked.headers["retry-after"]) > 0


def test_lockout_applies_even_to_the_correct_password(client):
    """Otherwise the throttle is bypassed by the one guess that matters."""
    from app.core.throttle import MAX_FAILURES

    for _ in range(MAX_FAILURES):
        client.post("/api/auth/login", json={"username": "admin", "password": "wrong"})

    r = client.post("/api/auth/login", json={"username": "admin", "password": PASSWORD})
    assert r.status_code == 429


def test_successful_login_clears_the_failure_count(client):
    """A user who mistypes twice and then succeeds must not stay one typo
    away from a lockout for the next fifteen minutes."""
    from app.core.throttle import MAX_FAILURES

    for _ in range(MAX_FAILURES - 1):
        client.post("/api/auth/login", json={"username": "admin", "password": "wrong"})

    assert client.post(
        "/api/auth/login", json={"username": "admin", "password": PASSWORD}
    ).status_code == 200

    # Budget is back: another wrong guess is a 401, not a 429.
    assert client.post(
        "/api/auth/login", json={"username": "admin", "password": "wrong"}
    ).status_code == 401


def test_lockout_is_per_username_not_global(client):
    """One attacker hammering 'ghost' must not lock the real admin out."""
    from app.core.throttle import MAX_FAILURES

    for _ in range(MAX_FAILURES + 1):
        client.post("/api/auth/login", json={"username": "ghost", "password": "wrong"})

    assert client.post(
        "/api/auth/login", json={"username": "admin", "password": PASSWORD}
    ).status_code == 200


def test_logout_clears_the_session(client):
    client.post("/api/auth/login", json={"username": "admin", "password": PASSWORD})
    assert client.post("/api/auth/logout").status_code == 204
    assert client.get("/api/auth/me").status_code == 401
