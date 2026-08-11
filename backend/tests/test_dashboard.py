"""Integration tests for the aggregation pipelines.

The pipelines run inside MongoDB, so they cannot be meaningfully faked — these
seed a scratch database and assert against real aggregation output. Skipped
when no MongoDB is reachable so the unit suite still runs anywhere.

    TEST_MONGO_URL=mongodb://127.0.0.1:27021 pytest
"""

import os
from datetime import datetime

import pytest

pytest_plugins = ("pytest_asyncio",)

TEST_MONGO_URL = os.environ.get("TEST_MONGO_URL", "mongodb://127.0.0.1:27017")


def _client():
    from pymongo import MongoClient

    return MongoClient(TEST_MONGO_URL, serverSelectionTimeoutMS=1500)


def _mongo_available() -> bool:
    try:
        _client().admin.command("ping")
        return True
    except Exception:
        return False


pytestmark = pytest.mark.skipif(
    not _mongo_available(), reason=f"no MongoDB at {TEST_MONGO_URL}"
)


@pytest.fixture
def db():
    """A scratch database seeded with a tiny, hand-checkable dataset."""
    from motor.motor_asyncio import AsyncIOMotorClient

    sync = _client()
    name = "dental_clinic_test"
    sync.drop_database(name)
    d = sync[name]

    d.invoices.insert_many([
        # 3 invoices across 2 months. Totals: 1000 + 500 + 300 = 1800
        {"invoice_id": 1, "issue_date": datetime(2026, 5, 10), "total_amount": 1000,
         "insurance_covered": 200, "patient_share": 800, "status": "پرداخت‌شده"},
        {"invoice_id": 2, "issue_date": datetime(2026, 6, 5), "total_amount": 500,
         "insurance_covered": 100, "patient_share": 400, "status": "بخشی"},
        {"invoice_id": 3, "issue_date": datetime(2026, 6, 20), "total_amount": 300,
         "insurance_covered": 0, "patient_share": 300, "status": "معوق"},
    ])
    d.payments.insert_many([
        {"payment_id": 1, "invoice_id": 1, "amount": 800, "payment_date": datetime(2026, 5, 12)},
        {"payment_id": 2, "invoice_id": 2, "amount": 150, "payment_date": datetime(2026, 6, 8)},
    ])
    d.consumables.insert_many([
        {"consumable_id": 1, "name": "بحرانی", "unit": "عدد", "stock_quantity": 5,
         "min_stock_level": 10, "unit_price": 100, "supplier": "الف"},
        {"consumable_id": 2, "name": "نزدیک", "unit": "عدد", "stock_quantity": 12,
         "min_stock_level": 10, "unit_price": 100, "supplier": "ب"},
        {"consumable_id": 3, "name": "کافی", "unit": "عدد", "stock_quantity": 100,
         "min_stock_level": 10, "unit_price": 100, "supplier": "ج"},
    ])
    # Sessions carry the same money as the invoices above, on the same dates.
    # The trend chart reads revenue from here — invoices say when the clinic
    # billed, sessions say when it did the work.
    d.treatment_sessions.insert_many([
        {"session_id": 1, "plan_id": 1, "service_id": 1, "actual_cost": 1000,
         "session_date": datetime(2026, 5, 10)},
        {"session_id": 2, "plan_id": 2, "service_id": 1, "actual_cost": 500,
         "session_date": datetime(2026, 6, 5)},
        {"session_id": 3, "plan_id": 3, "service_id": 1, "actual_cost": 300,
         "session_date": datetime(2026, 6, 20)},
    ])
    d.patients.insert_many([{"patient_id": i} for i in range(1, 26)])
    for c in ("appointments", "dentists"):
        d[c].insert_one({"_id": f"seed-{c}"})
    d.appointments.delete_many({})
    d.appointments.insert_many([
        {"appointment_id": 1, "status": "رزرو"},
        {"appointment_id": 2, "status": "رزرو"},
        {"appointment_id": 3, "status": "انجام‌شده"},
    ])

    motor = AsyncIOMotorClient(TEST_MONGO_URL)
    yield motor[name]
    motor.close()
    sync.drop_database(name)
    sync.close()


@pytest.mark.asyncio
async def test_summary_money_math(db):
    from app.repositories.dashboard import get_summary

    s = await get_summary(db)
    assert s["revenue"] == 1800
    assert s["insurance_covered"] == 300
    assert s["patient_share"] == 1500
    assert s["collected"] == 950
    assert s["outstanding"] == 1500 - 950
    # Rate is against patient_share, not revenue — the insurer's portion was
    # never the patient's to pay.
    assert s["collection_rate"] == round(950 / 1500 * 100)


@pytest.mark.asyncio
async def test_summary_counts(db):
    from app.repositories.dashboard import get_summary

    s = await get_summary(db)
    assert s["counts"]["patients"] == 25
    assert s["counts"]["appointments"] == 3
    assert s["counts"]["upcoming"] == 2  # status == "رزرو"


@pytest.mark.asyncio
async def test_revenue_trend_aligns_payments_to_delivered_months(db):
    """Regression: limiting revenue and payments to their own top-N months
    independently let them disagree, and a month present in one but not the
    other silently reported zero collected."""
    from app.repositories.dashboard import get_revenue_trend

    rows = await get_revenue_trend(db, months=12)
    assert [r["month"] for r in rows] == ["2026-05", "2026-06"]  # oldest first
    assert rows[0]["revenue"] == 1000
    assert rows[0]["collected"] == 800
    assert rows[1]["revenue"] == 800
    assert rows[1]["collected"] == 150


@pytest.mark.asyncio
async def test_revenue_trend_narrow_window_keeps_its_payments(db):
    """The exact shape of the bug: ask for 1 month and that month must still
    carry its own collections."""
    from app.repositories.dashboard import get_revenue_trend

    rows = await get_revenue_trend(db, months=1)
    assert len(rows) == 1
    assert rows[0]["month"] == "2026-06"
    assert rows[0]["collected"] == 150, "newest month lost its payments"


@pytest.mark.asyncio
async def test_revenue_trend_measures_delivery_not_billing(db):
    """The landing chart must agree with the analytics pages, which all sum
    session revenue. Sourcing it from invoice issue dates made a twelve-month
    trend collapse into however many months the billing run happened to touch."""
    from app.repositories.dashboard import get_revenue_trend

    # Same money, billed a year after it was earned.
    db_sync = _client()["dental_clinic_test"]
    db_sync.treatment_sessions.insert_one(
        {"session_id": 4, "plan_id": 4, "service_id": 1, "actual_cost": 700,
         "session_date": datetime(2025, 9, 3)})
    db_sync.invoices.insert_one(
        {"invoice_id": 4, "issue_date": datetime(2026, 6, 25), "total_amount": 700,
         "insurance_covered": 0, "patient_share": 700, "status": "معوق"})

    rows = await get_revenue_trend(db, months=12)
    months = {r["month"]: r["revenue"] for r in rows}
    assert months["2025-09"] == 700, "delivery month must appear, not the billing month"
    assert months["2026-06"] == 800, "billing must not inflate the month it was raised in"


@pytest.mark.asyncio
async def test_low_stock_flags_only_items_at_or_below_reorder_point(db):
    from app.repositories.dashboard import get_low_stock

    rows = await get_low_stock(db)
    by_name = {r["name"]: r for r in rows}
    assert "کافی" not in by_name, "well-stocked item should not be listed"
    assert by_name["بحرانی"]["critical"] is True
    assert by_name["نزدیک"]["critical"] is False
    assert rows[0]["name"] == "بحرانی", "critical items sort first"


@pytest.mark.asyncio
async def test_patient_pagination_meta(db):
    from app.repositories.records import list_patients

    first = await list_patients(db, page=1)
    assert first["meta"] == {"total": 25, "page": 1, "pages": 2, "size": 20}
    assert len(first["rows"]) == 20

    last = await list_patients(db, page=2)
    assert len(last["rows"]) == 5

    # Asking past the end clamps rather than returning an empty page.
    beyond = await list_patients(db, page=99)
    assert beyond["meta"]["page"] == 2
    assert len(beyond["rows"]) == 5


@pytest.mark.asyncio
async def test_patient_search_escapes_regex_metacharacters(db):
    """A user typing "(" must search for that character, not crash or scan."""
    from app.repositories.records import list_patients

    result = await list_patients(db, q="a(b[c")
    assert result["meta"]["total"] == 0
