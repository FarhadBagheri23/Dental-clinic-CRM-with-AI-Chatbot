"""Integration tests for the BI pipelines.

Focus is the derived metrics — revenue per chair-hour, commission margin,
loss rate. Those are where a wrong denominator produces a plausible number
that no one questions.
"""

import os
from datetime import datetime

import pytest

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
    from motor.motor_asyncio import AsyncIOMotorClient

    sync = _client()
    name = "dental_clinic_analytics_test"
    sync.drop_database(name)
    d = sync[name]

    d.services.insert_many([
        # 30-minute service: 4 sessions = 2 chair-hours
        {"service_id": 1, "name": "کوتاه", "category": "درمانی",
         "base_price": 100, "duration_minutes": 30},
        # 120-minute service: 1 session = 2 chair-hours, same revenue
        {"service_id": 2, "name": "بلند", "category": "جراحی",
         "base_price": 400, "duration_minutes": 120},
    ])
    d.dentists.insert_many([
        {"dentist_id": 1, "first_name": "الف", "last_name": "یک",
         "specialty": "عمومی", "commission_rate": 25.0},
        {"dentist_id": 2, "first_name": "ب", "last_name": "دو",
         "specialty": "جراح", "commission_rate": 50.0},
    ])
    d.treatment_plans.insert_many([
        {"plan_id": 1, "dentist_id": 1, "patient_id": 1},
        {"plan_id": 2, "dentist_id": 2, "patient_id": 2},
    ])
    d.treatment_sessions.insert_many([
        # dentist 1: 4 × 100 = 400 on the short service
        *[{"session_id": i, "plan_id": 1, "service_id": 1, "actual_cost": 100,
           "session_date": datetime(2026, 6, 10)} for i in range(1, 5)],
        # dentist 2: 1 × 400 on the long service
        {"session_id": 5, "plan_id": 2, "service_id": 2, "actual_cost": 400,
         "session_date": datetime(2026, 6, 11)},
    ])
    d.appointments.insert_many([
        {"appointment_id": 1, "dentist_id": 1, "status": "انجام‌شده", "chair_number": 1,
         "scheduled_datetime": datetime(2026, 6, 10, 9)},
        {"appointment_id": 2, "dentist_id": 1, "status": "لغو", "chair_number": 1,
         "scheduled_datetime": datetime(2026, 6, 10, 10)},
        {"appointment_id": 3, "dentist_id": 1, "status": "غایب", "chair_number": 2,
         "scheduled_datetime": datetime(2026, 6, 11, 9)},
        {"appointment_id": 4, "dentist_id": 2, "status": "انجام‌شده", "chair_number": 2,
         "scheduled_datetime": datetime(2026, 6, 11, 11)},
    ])
    d.payments.insert_many([
        {"payment_id": 1, "invoice_id": 1, "amount": 300, "method": "کارت",
         "payment_date": datetime(2026, 6, 12)},
        {"payment_id": 2, "invoice_id": 2, "amount": 100, "method": "نقد",
         "payment_date": datetime(2026, 6, 13)},
    ])
    d.invoices.insert_many([
        {"invoice_id": 1, "issue_date": datetime(2026, 6, 12), "total_amount": 800,
         "insurance_covered": 200, "patient_share": 600, "status": "بخشی"},
    ])

    motor = AsyncIOMotorClient(TEST_MONGO_URL)
    yield motor[name]
    motor.close()
    sync.drop_database(name)
    sync.close()


@pytest.mark.asyncio
async def test_revenue_per_chair_hour_reranks_services(db):
    """Both services earn 400 over 2 chair-hours, so revenue-per-hour ties —
    the point being that gross revenue alone would rank them differently
    from the volume-weighted view."""
    from app.repositories.analytics import service_mix
    from app.repositories.filters import Filters

    rows = {r["name"]: r for r in await service_mix(db, Filters())}

    assert rows["کوتاه"]["revenue"] == 400
    assert rows["کوتاه"]["sessions"] == 4
    assert rows["کوتاه"]["chair_hours"] == pytest.approx(2.0)   # 4 × 30min
    assert rows["کوتاه"]["revenue_per_hour"] == pytest.approx(200)
    assert rows["کوتاه"]["avg_ticket"] == pytest.approx(100)

    assert rows["بلند"]["chair_hours"] == pytest.approx(2.0)     # 1 × 120min
    assert rows["بلند"]["revenue_per_hour"] == pytest.approx(200)
    assert rows["بلند"]["avg_ticket"] == pytest.approx(400)


@pytest.mark.asyncio
async def test_dentist_margin_accounts_for_commission_rate(db):
    """The commission inversion: equal revenue, different clinic margin."""
    from app.repositories.analytics import dentist_scorecard
    from app.repositories.filters import Filters

    rows = {r["name"]: r for r in await dentist_scorecard(db, Filters())}
    a, b = rows["دکتر الف یک"], rows["دکتر ب دو"]

    assert a["revenue"] == b["revenue"] == 400
    assert a["commission"] == pytest.approx(100)   # 25%
    assert b["commission"] == pytest.approx(200)   # 50%
    assert a["margin"] == pytest.approx(300)
    assert b["margin"] == pytest.approx(200)
    assert a["margin"] > b["margin"], "equal revenue must not imply equal margin"


@pytest.mark.asyncio
async def test_dentist_reliability_rates(db):
    from app.repositories.analytics import dentist_scorecard
    from app.repositories.filters import Filters

    rows = {r["name"]: r for r in await dentist_scorecard(db, Filters())}
    # Dentist 1 has 3 appointments: 1 done, 1 cancelled, 1 no-show.
    assert rows["دکتر الف یک"]["cancel_rate"] == pytest.approx(33.3, abs=0.1)
    assert rows["دکتر الف یک"]["noshow_rate"] == pytest.approx(33.3, abs=0.1)
    assert rows["دکتر ب دو"]["cancel_rate"] == 0


@pytest.mark.asyncio
async def test_appointment_trend_loss_rate(db):
    from app.repositories.analytics import appointment_trend
    from app.repositories.filters import Filters

    rows = await appointment_trend(db, Filters())
    june = next(r for r in rows if r["month"] == "2026-06")
    assert june["total"] == 4
    assert june["cancelled"] == 1 and june["noshow"] == 1
    assert june["lost_rate"] == pytest.approx(50.0)


@pytest.mark.asyncio
async def test_specialty_filter_narrows_every_pipeline(db):
    from app.repositories.analytics import dentist_scorecard, revenue_by_category
    from app.repositories.filters import Filters

    surgeons = Filters(specialty="جراح")
    assert [r["name"] for r in await dentist_scorecard(db, surgeons)] == ["دکتر ب دو"]

    cats = await revenue_by_category(db, surgeons)
    assert [c["category"] for c in cats] == ["جراحی"]
    assert cats[0]["revenue"] == 400


@pytest.mark.asyncio
async def test_date_filter_excludes_out_of_range_sessions(db):
    from app.repositories.analytics import revenue_by_category
    from app.repositories.filters import Filters

    inside = await revenue_by_category(db, Filters(date_from=datetime(2026, 6, 1),
                                                  date_to=datetime(2026, 6, 30)))
    assert sum(c["revenue"] for c in inside) == 800

    outside = await revenue_by_category(db, Filters(date_from=datetime(2027, 1, 1)))
    assert outside == []


@pytest.mark.asyncio
async def test_receivables_chain_balances(db):
    from app.repositories.analytics import receivables
    from app.repositories.filters import Filters

    r = await receivables(db, Filters())
    assert r["billed"] == 800
    assert r["insurance"] + r["patient_share"] == r["billed"]
    assert r["collected"] == 400
    assert r["outstanding"] == r["patient_share"] - r["collected"]


@pytest.mark.asyncio
async def test_payment_methods_sum_to_collected(db):
    from app.repositories.analytics import payment_methods, receivables
    from app.repositories.filters import Filters

    methods = await payment_methods(db, Filters())
    assert sum(m["amount"] for m in methods) == (await receivables(db, Filters()))["collected"]


@pytest.mark.asyncio
async def test_chair_utilisation_reports_its_assumptions(db):
    """A bare percentage is unreadable without the capacity model behind it."""
    from app.repositories.analytics import chair_utilisation
    from app.repositories.filters import Filters

    result = await chair_utilisation(db, Filters())
    assert {c["chair"] for c in result["chairs"]} == {1, 2}
    assert result["booked_slots"] == 4
    assert set(result["assumptions"]) == {
        "chairs", "open_hour", "close_hour",
        "working_days_per_week", "slot_minutes", "weeks_in_window",
    }
