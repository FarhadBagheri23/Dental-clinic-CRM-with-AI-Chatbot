"""Filters must reach every pipeline, or say that they cannot.

Two failure modes are covered here, and they are opposites:

* A filter the user set is silently dropped, so a filtered heading sits above
  an unfiltered number. Six of eight analytics endpoints did exactly this.
* A filter is applied where it has no meaning, e.g. narrowing appointments by
  service category, which drops every cancellation (they have no session, so
  no service) and reports a 0% no-show rate.

The second case is declared in `UNSUPPORTED_FILTERS` and served to the client.
`test_declared_unsupported_filters_are_really_ignored` asserts every entry in
that map is true, so the declaration cannot drift away from the pipelines.
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

# Two insurers, two specialties and two categories, arranged so that every
# filter dimension splits the data unevenly — a filter that is silently
# dropped therefore cannot coincidentally produce the same numbers.
INSURER_A, INSURER_B = "بیمه الف", "بیمه ب"


@pytest.fixture
def db():
    from motor.motor_asyncio import AsyncIOMotorClient

    sync = _client()
    name = "dental_clinic_filters_test"
    sync.drop_database(name)
    d = sync[name]

    d.insurance.insert_many([
        {"insurance_id": 1, "company_name": INSURER_A, "coverage_percentage": 60},
        {"insurance_id": 2, "company_name": INSURER_B, "coverage_percentage": 30},
    ])
    d.patients.insert_many([
        {"patient_id": 1, "first_name": "الف", "last_name": "یک",
         "phone": "09120000001", "insurance_id": 1},
        {"patient_id": 2, "first_name": "ب", "last_name": "دو",
         "phone": "09120000002", "insurance_id": 2},
        # Registered, insured by A, and never treated: no plan, no session.
        {"patient_id": 3, "first_name": "ج", "last_name": "سه",
         "phone": "09120000003", "insurance_id": 1},
    ])
    d.dentists.insert_many([
        {"dentist_id": 1, "first_name": "دکتر", "last_name": "الف",
         "specialty": "عمومی", "commission_rate": 30.0},
        {"dentist_id": 2, "first_name": "دکتر", "last_name": "ب",
         "specialty": "جراح", "commission_rate": 40.0},
    ])
    d.services.insert_many([
        {"service_id": 1, "name": "معاینه", "category": "درمانی",
         "base_price": 100, "duration_minutes": 30},
        {"service_id": 2, "name": "جراحی لثه", "category": "جراحی",
         "base_price": 500, "duration_minutes": 60},
    ])
    d.treatment_plans.insert_many([
        {"plan_id": 1, "patient_id": 1, "dentist_id": 1, "status": "فعال",
         "start_date": datetime(2026, 6, 1),
         "estimated_end_date": datetime(2026, 6, 30), "total_estimated_cost": 100},
        {"plan_id": 2, "patient_id": 2, "dentist_id": 2, "status": "تکمیل‌شده",
         "start_date": datetime(2026, 6, 2),
         "estimated_end_date": datetime(2026, 6, 20), "total_estimated_cost": 500},
    ])
    d.treatment_sessions.insert_many([
        {"session_id": 1, "plan_id": 1, "service_id": 1, "appointment_id": 1,
         "actual_cost": 100, "session_date": datetime(2026, 6, 10)},
        {"session_id": 2, "plan_id": 2, "service_id": 2, "appointment_id": 2,
         "actual_cost": 500, "session_date": datetime(2026, 6, 11)},
    ])
    d.appointments.insert_many([
        {"appointment_id": 1, "patient_id": 1, "dentist_id": 1, "chair_number": 1,
         "status": "انجام‌شده", "scheduled_datetime": datetime(2026, 6, 10, 9)},
        {"appointment_id": 2, "patient_id": 2, "dentist_id": 2, "chair_number": 2,
         "status": "انجام‌شده", "scheduled_datetime": datetime(2026, 6, 11, 10)},
        # Cancelled and no-show carry no session, so no service category.
        {"appointment_id": 3, "patient_id": 1, "dentist_id": 1, "chair_number": 1,
         "status": "لغو", "scheduled_datetime": datetime(2026, 6, 12, 9)},
        {"appointment_id": 4, "patient_id": 2, "dentist_id": 2, "chair_number": 2,
         "status": "غایب", "scheduled_datetime": datetime(2026, 6, 13, 10)},
    ])
    d.invoices.insert_many([
        {"invoice_id": 1, "patient_id": 1, "plan_id": 1,
         "issue_date": datetime(2026, 6, 12), "total_amount": 100,
         "insurance_covered": 60, "patient_share": 40, "status": "پرداخت‌شده"},
        {"invoice_id": 2, "patient_id": 2, "plan_id": 2,
         "issue_date": datetime(2026, 6, 13), "total_amount": 500,
         "insurance_covered": 150, "patient_share": 350, "status": "بخشی"},
    ])
    d.payments.insert_many([
        {"payment_id": 1, "invoice_id": 1, "amount": 40, "method": "نقد",
         "payment_date": datetime(2026, 6, 14)},
        {"payment_id": 2, "invoice_id": 2, "amount": 100, "method": "کارت",
         "payment_date": datetime(2026, 6, 15)},
    ])
    d.clinic_capacity.insert_many([
        {"chair_number": 1, "start_hour": 9, "end_hour": 17, "staffed_hours_per_day": 8},
        {"chair_number": 2, "start_hour": 9, "end_hour": 13, "staffed_hours_per_day": 4},
    ])

    motor = AsyncIOMotorClient(TEST_MONGO_URL)
    yield motor[name]
    motor.close()
    sync.drop_database(name)
    sync.close()


def _endpoints():
    """Endpoint path segment -> the repository call behind it."""
    from app.repositories import analytics as A

    return {
        "appointment-trend": A.appointment_trend,
        "heatmap": A.hourly_heatmap,
        "lost-slots": A.lost_slot_cost,
        "receivables": A.receivables,
        "payment-methods": A.payment_methods,
        "treatment-plans": A.treatment_plans,
        "aging": A.receivables_aging,
    }


# A value that exists in the fixture for each filter, so setting it genuinely
# selects a subset rather than matching nothing.
FILTER_VALUES = {"specialty": "جراح", "category": "جراحی", "insurance": INSURER_A}


@pytest.mark.asyncio
@pytest.mark.parametrize("endpoint,filter_name", [
    (ep, name)
    for ep, names in __import__(
        "app.repositories.filters", fromlist=["UNSUPPORTED_FILTERS"]
    ).UNSUPPORTED_FILTERS.items()
    for name in names
])
async def test_declared_unsupported_filters_are_really_ignored(db, endpoint, filter_name):
    """Every entry in UNSUPPORTED_FILTERS must be a fact, not a stale note.

    If someone later teaches a pipeline to honour the filter, this fails and
    the map has to be updated — which is the point. The client shows a
    "this filter does not apply here" note based on that map, and a note that
    lies is worse than no note.
    """
    from app.repositories.filters import Filters

    call = _endpoints()[endpoint]
    baseline = await call(db, Filters())
    filtered = await call(db, Filters(**{filter_name: FILTER_VALUES[filter_name]}))

    assert filtered == baseline, (
        f"{endpoint} now responds to {filter_name}; remove it from "
        f"UNSUPPORTED_FILTERS so the UI stops claiming it is ignored"
    )


@pytest.mark.asyncio
@pytest.mark.parametrize("endpoint,filter_name", [
    ("receivables", "insurance"),
    ("receivables", "specialty"),
    ("payment-methods", "insurance"),
    ("payment-methods", "specialty"),
    ("appointment-trend", "insurance"),
    ("appointment-trend", "specialty"),
    ("heatmap", "insurance"),
    ("treatment-plans", "insurance"),
    ("lost-slots", "insurance"),
    ("aging", "insurance"),
    ("aging", "specialty"),
])
async def test_supported_filters_actually_narrow_the_result(db, endpoint, filter_name):
    """The regression that started this: these combinations were silently
    dropped, so the panel showed clinic-wide totals under a filtered header."""
    from app.repositories.filters import Filters

    call = _endpoints()[endpoint]
    baseline = await call(db, Filters())
    filtered = await call(db, Filters(**{filter_name: FILTER_VALUES[filter_name]}))

    assert filtered != baseline, f"{endpoint} ignores {filter_name}"


@pytest.mark.asyncio
async def test_never_treated_counts_patients_not_the_filtered_remainder(db):
    """Only patient 3 has no session at all.

    The old implementation computed `all_patients - treated_in_window`, so
    filtering to one insurer reported the other insurer's patients as
    "registered, never treated" — the tighter the filter, the bigger the
    number, which is backwards.
    """
    from app.repositories.analytics import patient_recall
    from app.repositories.filters import Filters

    assert (await patient_recall(db, Filters()))["never_treated"] == 1

    # Patients 1 and 3 are insured by A; only 3 was never treated.
    by_insurer = await patient_recall(db, Filters(insurance=INSURER_A))
    assert by_insurer["never_treated"] == 1
    assert by_insurer["active"] == 1

    # Insurer B has patient 2, who was treated, so nobody is untreated.
    assert (await patient_recall(db, Filters(insurance=INSURER_B)))["never_treated"] == 0


@pytest.mark.asyncio
async def test_recall_status_is_as_of_today_not_relative_to_the_window(db):
    """Looking at an old period must not invent lapsed patients.

    Recall asks "has this patient been seen in the last 180 days", which is a
    fact about today. Deriving last-visit from only the sessions inside the
    window made a 2025 filter report 0% recall and every patient lapsed.
    """
    from app.repositories.analytics import patient_recall
    from app.repositories.filters import Filters

    unfiltered = await patient_recall(db, Filters())
    old_window = await patient_recall(
        db, Filters(date_from=datetime(2025, 1, 1), date_to=datetime(2025, 3, 1))
    )

    assert old_window["lapsed"] == unfiltered["lapsed"]
    assert old_window["active"] == unfiltered["active"]
    assert old_window["recall_rate"] == unfiltered["recall_rate"]


@pytest.mark.asyncio
async def test_category_filter_would_erase_cancellations(db):
    """Why category is unsupported on appointment pipelines.

    The fixture has one cancellation and one no-show, neither with a session.
    The loss rate must stay put when a category is requested, rather than
    quietly becoming 0% because the only surviving rows were completed ones.
    """
    from app.repositories.analytics import lost_slot_cost
    from app.repositories.filters import Filters

    baseline = await lost_slot_cost(db, Filters())
    assert baseline["lost_slots"] == 2
    assert baseline["cancelled"] == 1 and baseline["noshow"] == 1

    filtered = await lost_slot_cost(db, Filters(category="جراحی"))
    assert filtered["lost_slots"] == 2, "category filter erased the lost slots"


@pytest.mark.asyncio
async def test_material_cost_does_not_multiply_revenue_per_usage_row(db):
    """A session using three materials must count its revenue once.

    Rooting the pipeline at consumable_usage produced one row per material,
    so `$sum: actual_cost` counted a 500-toman session three times and made
    material cost look like a third of its true share of revenue.
    """
    from app.repositories.analytics import consumable_cost_by_category
    from app.repositories.filters import Filters

    db_sync = _client()["dental_clinic_filters_test"]
    db_sync.consumables.insert_many([
        {"consumable_id": i, "name": f"ماده {i}", "unit_price": 10,
         "unit": "عدد", "stock_quantity": 5, "min_stock_level": 2}
        for i in (1, 2, 3)
    ])
    db_sync.consumable_usage.insert_many([
        {"usage_id": i, "consumable_id": i, "session_id": 2, "quantity_used": 1,
         "usage_date": datetime(2026, 6, 11)}
        for i in (1, 2, 3)
    ])

    rows = {r["category"]: r for r in await consumable_cost_by_category(db, Filters())}

    # Session 2 alone: revenue counted once, all three materials counted.
    assert rows["جراحی"]["revenue"] == 500
    assert rows["جراحی"]["cost"] == 30
