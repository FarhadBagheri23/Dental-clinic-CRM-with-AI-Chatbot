"""Non-owner roles must not receive patient contacts or commission figures.

This used to be enforced only by a line in the assistant's system prompt
asking the model not to mention them. That is not an access control for two
reasons: a model can be talked past its instructions, and the same rows were
available from the REST API, which had no role check at all. These tests
assert the data is withheld, not that something was asked politely.
"""

import pytest
from fastapi.testclient import TestClient

from app.api.deps import SESSION_COOKIE
from app.core.redaction import PLACEHOLDER, is_owner, scrub
from app.core.security import create_token
from app.db.mongodb import get_db
from app.main import app

OWNER = {"username": "admin", "display_name": "مدیر سیستم", "role": "مدیر"}
STAFF = {"username": "reception", "display_name": "پذیرش", "role": "کاربر"}


# ------------------------------------------------------------ unit level

def test_is_owner_only_accepts_the_owner_role():
    assert is_owner({"role": "مدیر"})
    assert not is_owner({"role": "کاربر"})
    assert not is_owner({})


def test_scrub_replaces_named_fields_and_leaves_the_rest():
    rows = [{"name": "علی", "phone": "09120000000", "revenue": 500}]
    out = scrub(rows, ("name", "phone"))

    assert out == [{"name": PLACEHOLDER, "phone": PLACEHOLDER, "revenue": 500}]
    # Aggregates survive: a receptionist still sees the number, not the person.
    assert out[0]["revenue"] == 500


def test_scrub_does_not_mutate_the_caller_rows():
    """These dicts come straight from a repository and may be shared."""
    rows = [{"name": "علی", "revenue": 500}]
    scrub(rows, ("name",))
    assert rows[0]["name"] == "علی"


# ------------------------------------------------------------- endpoints

class FakeCursor:
    def __init__(self, rows):
        self._rows = rows

    async def to_list(self, _n):
        return self._rows


class FakeCollection:
    def __init__(self, rows=None):
        self._rows = rows or []

    def aggregate(self, _pipeline):
        return FakeCursor(self._rows)

    async def count_documents(self, _q):
        return len(self._rows)

    async def find_one(self, _q):
        return None

    async def create_index(self, *a, **k):
        return None

    def find(self, *a, **k):
        return self

    def sort(self, *a, **k):
        return self

    async def to_list(self, _n):
        return self._rows


class FakeDB:
    """Rows per collection name.

    `dentist_scorecard` runs two aggregates with different shapes — the
    scorecard over treatment_sessions and the reliability rates over
    appointments — so a fake that answered both identically would raise
    rather than exercise the redaction.
    """

    def __init__(self, by_collection):
        self._by = by_collection

    def __getattr__(self, name):
        return FakeCollection(self._by.get(name, []))

    def __getitem__(self, name):
        return FakeCollection(self._by.get(name, []))


DENTIST_ROW = {
    "dentist_id": 1, "name": "دکتر الف", "specialty": "عمومی",
    "revenue": 1000, "sessions": 10, "patients": 5,
    "commission_rate": 30.0, "commission": 300.0, "margin": 700.0,
}
RELIABILITY_ROW = {"_id": 1, "total": 10, "cancelled": 1, "noshow": 1}


@pytest.fixture
def client():
    db = FakeDB({
        "treatment_sessions": [DENTIST_ROW],
        "appointments": [RELIABILITY_ROW],
    })
    app.dependency_overrides[get_db] = lambda: db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


def _as(client, user):
    client.cookies.set(SESSION_COOKIE, create_token(user))
    return client


def test_owner_sees_commission_and_margin(client):
    row = _as(client, OWNER).get("/api/analytics/dentists").json()[0]

    assert row["commission_rate"] == 30.0
    assert row["margin"] == 700.0


def test_non_owner_does_not_receive_commission_or_margin(client):
    """The receptionist still gets revenue and reliability — the useful part —
    but what each colleague personally earns is withheld."""
    row = _as(client, STAFF).get("/api/analytics/dentists").json()[0]

    assert row["commission_rate"] == PLACEHOLDER
    assert row["commission"] == PLACEHOLDER
    assert row["margin"] == PLACEHOLDER
    assert row["revenue"] == 1000, "revenue is not sensitive and must survive"
    assert row["specialty"] == "عمومی"


def test_redaction_survives_json_serialisation(client):
    """A placeholder that leaked the real value in a nested structure would
    defeat the point, so this asserts against the raw response body."""
    body = _as(client, STAFF).get("/api/analytics/dentists").text

    assert "700" not in body
    assert "30.0" not in body
