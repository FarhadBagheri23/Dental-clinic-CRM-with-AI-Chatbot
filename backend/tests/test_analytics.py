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
    d.patients.insert_many([
        {"patient_id": 1, "first_name": "بیمار", "last_name": "یک", "phone": "09120000001"},
        {"patient_id": 2, "first_name": "بیمار", "last_name": "دو", "phone": "09120000002"},
        # Registered but never treated — has no session, so no plan either.
        {"patient_id": 3, "first_name": "بیمار", "last_name": "سه", "phone": "09120000003"},
    ])
    d.treatment_plans.insert_many([
        # Open and past its estimated end: 400 quoted, 400 delivered.
        {"plan_id": 1, "dentist_id": 1, "patient_id": 1, "status": "فعال",
         "start_date": datetime(2026, 6, 1), "estimated_end_date": datetime(2026, 6, 30),
         "total_estimated_cost": 1000},
        {"plan_id": 2, "dentist_id": 2, "patient_id": 2, "status": "تکمیل‌شده",
         "start_date": datetime(2026, 6, 1), "estimated_end_date": datetime(2026, 6, 20),
         "total_estimated_cost": 400},
        # Quoted and refused — the only thing that lowers case acceptance.
        {"plan_id": 3, "dentist_id": 1, "patient_id": 2, "status": "لغو",
         "start_date": datetime(2026, 6, 1), "estimated_end_date": datetime(2026, 6, 25),
         "total_estimated_cost": 600},
    ])
    d.treatment_sessions.insert_many([
        # dentist 1: 4 × 100 = 400 on the short service. Only the first is tied
        # to an appointment; the rest deliberately are not, so the chair
        # pipeline is also exercised against sessions it must skip.
        {"session_id": 1, "plan_id": 1, "service_id": 1, "actual_cost": 100,
         "appointment_id": 1, "session_date": datetime(2026, 6, 10)},
        *[{"session_id": i, "plan_id": 1, "service_id": 1, "actual_cost": 100,
           "session_date": datetime(2026, 6, 10)} for i in range(2, 5)],
        # dentist 2: 1 × 400 on the long service, in chair 2
        {"session_id": 5, "plan_id": 2, "service_id": 2, "actual_cost": 400,
         "appointment_id": 4, "session_date": datetime(2026, 6, 11)},
    ])
    # Deliberately uneven shifts: utilisation must not assume interchangeable chairs.
    d.clinic_capacity.insert_many([
        {"chair_number": 1, "start_hour": 9, "end_hour": 17, "staffed_hours_per_day": 8},
        {"chair_number": 2, "start_hour": 14, "end_hour": 18, "staffed_hours_per_day": 4},
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
    # Cash that arrived in the window. Payment 2 belongs to invoice 2, which
    # does not exist, so only payment 1's 300 is matched to a window invoice.
    assert r["collected"] == 400
    assert r["collected_on_window_invoices"] == 300
    # The waterfall must balance: insurance + collected + outstanding = billed.
    assert r["outstanding"] == r["patient_share"] - r["collected_on_window_invoices"]
    assert r["insurance"] + r["collected_on_window_invoices"] + r["outstanding"] == r["billed"]


@pytest.mark.asyncio
async def test_collection_rate_cannot_exceed_100_on_a_filtered_window(db):
    """Regression: dividing cash received in a window by what was billed in
    that window compares two different cohorts, and reported 441% for a month
    whose payments were settling older invoices."""
    from app.repositories.analytics import receivables
    from app.repositories.filters import Filters

    june = Filters(date_from=datetime(2026, 6, 1), date_to=datetime(2026, 6, 30))
    r = await receivables(db, june)
    assert 0 <= r["collection_rate"] <= 100, r["collection_rate"]


@pytest.mark.asyncio
async def test_payment_methods_sum_to_collected(db):
    from app.repositories.analytics import payment_methods, receivables
    from app.repositories.filters import Filters

    methods = await payment_methods(db, Filters())
    assert sum(m["amount"] for m in methods) == (await receivables(db, Filters()))["collected"]


@pytest.mark.asyncio
async def test_chair_utilisation_measures_real_minutes_not_slot_counts(db):
    """Booked time comes from the session -> appointment (which chair) and
    session -> service (how long) relations. Counting appointments as equal
    30-minute slots understates a 120-minute surgery by a factor of four."""
    from app.repositories.analytics import chair_utilisation
    from app.repositories.filters import Filters

    by_chair = {c["chair"]: c for c in (await chair_utilisation(db, Filters()))["chairs"]}

    # Chair 1 ran session 1 only: the 30-minute service.
    assert by_chair[1]["sessions"] == 1
    assert by_chair[1]["booked_hours"] == pytest.approx(0.5)
    # Chair 2 ran session 5: the 120-minute service. A slot-count model would
    # have called these two chairs equally busy.
    assert by_chair[2]["sessions"] == 1
    assert by_chair[2]["booked_hours"] == pytest.approx(2.0)


@pytest.mark.asyncio
async def test_chair_utilisation_divides_by_staffed_hours(db):
    """Capacity is what the roster covers, not chairs x opening hours — chair 2
    is staffed for half as long as chair 1, so the same booked hour on it is
    worth twice the utilisation."""
    from app.repositories.analytics import chair_utilisation
    from app.repositories.filters import Filters

    result = await chair_utilisation(db, Filters())
    by_chair = {c["chair"]: c for c in result["chairs"]}

    assert by_chair[1]["staffed_hours_per_day"] == 8
    assert by_chair[2]["staffed_hours_per_day"] == 4
    # capacity_hours is rounded to one decimal for display, so compare within
    # that tolerance rather than asserting exact halves.
    assert by_chair[2]["capacity_hours"] == pytest.approx(
        by_chair[1]["capacity_hours"] / 2, abs=0.1)
    assert result["assumptions"]["staffed_hours_per_day"] == 12   # 8 + 4, not 2 x 12
    assert result["assumptions"]["source"] == "clinic_capacity"
    # The ratio the page prints must be the one the parts add up to.
    assert result["booked_hours"] == round(
        sum(c["booked_hours"] for c in result["chairs"]))


# ------------------------------------------------------ clinical metrics

@pytest.mark.asyncio
async def test_case_acceptance_counts_only_refused_plans_against_it(db):
    """Acceptance is the complement of cancellation, and completion is its own
    number — conflating the two overstates how much treatment finished."""
    from app.repositories.analytics import treatment_plans
    from app.repositories.filters import Filters

    p = await treatment_plans(db, Filters())
    assert p["total_plans"] == 3
    assert p["acceptance_rate"] == pytest.approx(66.7, abs=0.1)   # 2 of 3 not cancelled
    assert p["completion_rate"] == pytest.approx(33.3, abs=0.1)   # 1 of 3 completed
    assert p["planned_value"] == 2000
    assert p["delivered_value"] == 800                            # 400 + 400 in sessions


@pytest.mark.asyncio
async def test_unrealised_value_covers_open_plans_only(db):
    """The point of the metric: treatment the patient agreed to that has not
    been done. A cancelled plan is not owed work, so it must not inflate it."""
    from app.repositories.analytics import treatment_plans
    from app.repositories.filters import Filters

    p = await treatment_plans(db, Filters())
    # Plan 1 alone is open: 1000 quoted - 400 delivered. Plan 3 (600, cancelled)
    # and plan 2 (completed) contribute nothing.
    assert p["unrealised_value"] == 600
    assert p["overdue_count"] == 1
    assert p["overdue_value"] == 600
    assert [r["patient"] for r in p["overdue_plans"]] == ["بیمار یک"]
    assert p["overdue_plans"][0]["days_overdue"] > 0


@pytest.mark.asyncio
async def test_recall_separates_never_treated_from_lapsed(db):
    """A patient who never came back and one who never started are different
    problems — averaging them into "total patients" hides both."""
    from app.repositories.analytics import patient_recall
    from app.repositories.filters import Filters

    r = await patient_recall(db, Filters())
    assert r["never_treated"] == 1          # patient 3, registered with no session
    assert r["active"] + r["lapsed"] == 2   # patients 1 and 2 were treated
    # June 2026 is every patient's first month, so nobody is returning yet.
    june = next(m for m in r["new_vs_returning"] if m["month"] == "2026-06")
    assert june["new"] == 2 and june["returning"] == 0


@pytest.mark.asyncio
async def test_lost_slots_priced_at_the_average_session(db):
    """The percentage and the toman figure must come from the same slots."""
    from app.repositories.analytics import lost_slot_cost
    from app.repositories.filters import Filters

    r = await lost_slot_cost(db, Filters())
    assert r["cancelled"] == 1 and r["noshow"] == 1
    assert r["lost_slots"] == 2
    assert r["lost_rate"] == pytest.approx(50.0)
    assert r["avg_session_value"] == 160          # 800 over 5 sessions
    assert r["lost_revenue"] == 2 * 160
    assert r["lost_chair_hours"] == pytest.approx(1.0)   # 2 × 30min
