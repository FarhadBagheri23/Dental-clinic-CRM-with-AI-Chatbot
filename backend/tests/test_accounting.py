"""A/R ageing, DSO and per-service profitability.

Every number here is hand-computable from the fixture, because these are the
figures an accountant will check against their own spreadsheet — a test that
merely asserts "returns a float" would not have caught the revenue
multiplication bug that motivated the per-session collapse in these
pipelines.
"""

import os
from datetime import UTC, datetime, timedelta

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

NOW = datetime.now(UTC)


def _days_ago(n: int) -> datetime:
    # Naive, because that is how Mongo stores and returns dates.
    return (NOW - timedelta(days=n)).replace(tzinfo=None)


@pytest.fixture
def db():
    from motor.motor_asyncio import AsyncIOMotorClient

    sync = _client()
    name = "dental_clinic_accounting_test"
    sync.drop_database(name)
    d = sync[name]

    d.services.insert_many([
        # 1000 list price, and a session is billed at 900 -> 100 discount.
        {"service_id": 1, "name": "ترمیم", "category": "درمانی",
         "base_price": 1000, "duration_minutes": 60},
        # Deliberately loss-making: 200 billed, 150 material, 40% commission.
        {"service_id": 2, "name": "فلوراید", "category": "پیشگیری",
         "base_price": 200, "duration_minutes": 30},
    ])
    d.dentists.insert_many([
        {"dentist_id": 1, "first_name": "دکتر", "last_name": "الف",
         "specialty": "عمومی", "commission_rate": 40.0},
    ])
    d.patients.insert_many([
        {"patient_id": 1, "first_name": "الف", "last_name": "یک", "phone": "0912"},
        {"patient_id": 2, "first_name": "ب", "last_name": "دو", "phone": "0913"},
    ])
    d.treatment_plans.insert_many([
        {"plan_id": 1, "patient_id": 1, "dentist_id": 1, "status": "فعال",
         "start_date": _days_ago(120), "estimated_end_date": _days_ago(10),
         "total_estimated_cost": 1100},
    ])
    d.treatment_sessions.insert_many([
        {"session_id": 1, "plan_id": 1, "service_id": 1, "appointment_id": 1,
         "actual_cost": 900, "session_date": _days_ago(100)},
        {"session_id": 2, "plan_id": 1, "service_id": 2, "appointment_id": 2,
         "actual_cost": 200, "session_date": _days_ago(20)},
    ])
    # Session 2 burns three materials at 50 each = 150, which alone exceeds
    # what is left after the 40% commission on 200.
    d.consumables.insert_many([
        {"consumable_id": i, "name": f"ماده {i}", "unit_price": 50, "unit": "عدد",
         "stock_quantity": 10, "min_stock_level": 2} for i in (1, 2, 3)
    ])
    d.consumable_usage.insert_many([
        {"usage_id": i, "consumable_id": i, "session_id": 2, "quantity_used": 1,
         "usage_date": _days_ago(20)} for i in (1, 2, 3)
    ])
    d.staff.insert_many([
        {"staff_id": 1, "role": "پذیرش", "salary": 100, "hire_date": _days_ago(400)},
        {"staff_id": 2, "role": "دستیار", "salary": 200, "hire_date": _days_ago(400)},
    ])
    # Ageing ladder: one invoice per bucket, each partly or wholly unpaid.
    d.invoices.insert_many([
        {"invoice_id": 1, "patient_id": 1, "plan_id": 1, "issue_date": _days_ago(10),
         "total_amount": 500, "insurance_covered": 0, "patient_share": 500,
         "status": "بخشی"},
        {"invoice_id": 2, "patient_id": 1, "plan_id": 1, "issue_date": _days_ago(45),
         "total_amount": 300, "insurance_covered": 0, "patient_share": 300,
         "status": "پرداخت‌نشده"},
        {"invoice_id": 3, "patient_id": 2, "plan_id": 1, "issue_date": _days_ago(75),
         "total_amount": 200, "insurance_covered": 0, "patient_share": 200,
         "status": "پرداخت‌نشده"},
        {"invoice_id": 4, "patient_id": 2, "plan_id": 1, "issue_date": _days_ago(200),
         "total_amount": 400, "insurance_covered": 0, "patient_share": 400,
         "status": "پرداخت‌نشده"},
        # Fully settled 5 days after issue — the only input to avg_days_to_settle.
        {"invoice_id": 5, "patient_id": 1, "plan_id": 1, "issue_date": _days_ago(30),
         "total_amount": 100, "insurance_covered": 0, "patient_share": 100,
         "status": "پرداخت‌شده"},
    ])
    d.payments.insert_many([
        {"payment_id": 1, "invoice_id": 1, "amount": 200, "method": "نقد",
         "payment_date": _days_ago(8)},
        {"payment_id": 2, "invoice_id": 5, "amount": 100, "method": "کارت",
         "payment_date": _days_ago(25)},
    ])

    motor = AsyncIOMotorClient(TEST_MONGO_URL)
    yield motor[name]
    motor.close()
    sync.drop_database(name)
    sync.close()


# ------------------------------------------------------------- A/R ageing

@pytest.mark.asyncio
async def test_ageing_buckets_split_by_invoice_age(db):
    """Outstanding totals 1200, spread across four buckets.

    invoice 1: 500 billed - 200 paid = 300 open, 10 days   -> 0-30
    invoice 2: 300 open, 45 days                           -> 31-60
    invoice 3: 200 open, 75 days                           -> 61-90
    invoice 4: 400 open, 200 days                          -> 90+
    invoice 5: fully paid, so it is not receivable at all.
    """
    from app.repositories.analytics import receivables_aging
    from app.repositories.filters import Filters

    d = await receivables_aging(db, Filters())
    buckets = {b["bucket"]: b for b in d["buckets"]}

    assert d["outstanding"] == 1200
    assert buckets["۰ تا ۳۰ روز"]["amount"] == 300
    assert buckets["۳۱ تا ۶۰ روز"]["amount"] == 300
    assert buckets["۶۱ تا ۹۰ روز"]["amount"] == 200
    assert buckets["بیش از ۹۰ روز"]["amount"] == 400
    assert buckets["بیش از ۹۰ روز"]["n"] == 1

    # 400 of 1200 is older than ninety days.
    assert d["over_90_share"] == pytest.approx(33.3, abs=0.1)


@pytest.mark.asyncio
async def test_fully_paid_invoice_is_not_receivable(db):
    """Invoice 5 is settled, so it must appear in neither the buckets nor the
    chase list, however recently it was issued."""
    from app.repositories.analytics import receivables_aging
    from app.repositories.filters import Filters

    d = await receivables_aging(db, Filters())

    assert sum(b["n"] for b in d["buckets"]) == 4
    assert 5 not in [r["invoice_id"] for r in d["worst"]]


@pytest.mark.asyncio
async def test_avg_days_to_settle_uses_only_invoices_with_payments(db):
    """Invoice 1 settled partially after 2 days, invoice 5 fully after 5.

    Unpaid invoices must not enter the average as zeros — that would report
    a clinic collecting faster the more bills it fails to collect.
    """
    from app.repositories.analytics import receivables_aging
    from app.repositories.filters import Filters

    d = await receivables_aging(db, Filters())

    assert d["avg_days_to_settle"] == pytest.approx(3.5, abs=0.1)


@pytest.mark.asyncio
async def test_worst_list_is_ordered_by_balance_not_age(db):
    """Collection time is finite: the biggest debt is chased before the
    oldest one. Invoice 4 (400) outranks invoice 2 (300) and invoice 1 (300)."""
    from app.repositories.analytics import receivables_aging
    from app.repositories.filters import Filters

    d = await receivables_aging(db, Filters())

    assert [r["balance"] for r in d["worst"]] == [400, 300, 300, 200]


@pytest.mark.asyncio
async def test_overpaid_invoice_does_not_cancel_out_real_debt(db):
    """A credit is money to refund, not negative debt.

    Netting it off would understate receivables and hide a real arrear behind
    someone else's overpayment.
    """
    from app.repositories.analytics import receivables_aging
    from app.repositories.filters import Filters

    _client()["dental_clinic_accounting_test"].payments.insert_one(
        {"payment_id": 99, "invoice_id": 3, "amount": 1000, "method": "نقد",
         "payment_date": _days_ago(1)}
    )

    d = await receivables_aging(db, Filters())

    # Invoice 3 (200 share, 1000 paid) drops out; the other three remain.
    assert d["outstanding"] == 1000


# --------------------------------------------------------- profitability

@pytest.mark.asyncio
async def test_service_margin_subtracts_material_and_commission(db):
    """ترمیم: 900 revenue, no material, 40% commission = 360 -> 540 margin.
    فلوراید: 200 revenue, 150 material, 80 commission -> -30, a real loss."""
    from app.repositories.analytics import profitability
    from app.repositories.filters import Filters

    d = await profitability(db, Filters())
    by_name = {s["name"]: s for s in d["services"]}

    assert by_name["ترمیم"]["commission"] == 360
    assert by_name["ترمیم"]["material_cost"] == 0
    assert by_name["ترمیم"]["gross_margin"] == 540
    assert by_name["ترمیم"]["margin_pct"] == pytest.approx(60.0)

    assert by_name["فلوراید"]["material_cost"] == 150
    assert by_name["فلوراید"]["commission"] == 80
    assert by_name["فلوراید"]["gross_margin"] == -30


@pytest.mark.asyncio
async def test_loss_making_services_sort_to_the_top(db):
    """This table exists to surface the services that are busy rather than
    profitable, and those sink to the bottom of every revenue-ranked view."""
    from app.repositories.analytics import profitability
    from app.repositories.filters import Filters

    d = await profitability(db, Filters())

    assert d["services"][0]["name"] == "فلوراید"


@pytest.mark.asyncio
async def test_material_cost_counts_revenue_once_per_session(db):
    """فلوراید used three materials. Rooting at consumable_usage would have
    reported 600 revenue for one 200-toman session."""
    from app.repositories.analytics import profitability
    from app.repositories.filters import Filters

    d = await profitability(db, Filters())
    fluoride = next(s for s in d["services"] if s["name"] == "فلوراید")

    assert fluoride["revenue"] == 200
    assert fluoride["sessions"] == 1


@pytest.mark.asyncio
async def test_discount_is_list_price_minus_billed(db):
    """ترمیم listed at 1000 and billed at 900; فلوراید listed and billed at
    200. The 100 difference is margin given away at the desk and appears on
    no other report."""
    from app.repositories.analytics import profitability
    from app.repositories.filters import Filters

    d = await profitability(db, Filters())

    assert d["discount"]["list_value"] == 1200
    assert d["discount"]["billed"] == 1100
    assert d["discount"]["given_away"] == 100


@pytest.mark.asyncio
async def test_payroll_is_apportioned_across_the_window(db):
    """300/month of salary over an 80-day window is roughly 2.6 months of it.

    Reporting the raw monthly figure against a year of revenue would make
    payroll look like a rounding error.
    """
    from app.repositories.analytics import profitability
    from app.repositories.filters import Filters

    d = await profitability(
        db, Filters(date_from=NOW - timedelta(days=100), date_to=NOW)
    )

    assert d["payroll"]["headcount"] == 2
    assert d["payroll"]["monthly"] == 300
    # 100 days / 30.44 = 3.29 months x 300 ~= 986
    assert d["payroll"]["window_cost"] == pytest.approx(986, abs=2)


@pytest.mark.asyncio
async def test_operating_margin_is_below_gross_margin(db):
    """Payroll is a clinic-wide overhead, so it is subtracted once at the
    total level and never split across services — apportioning a receptionist
    between a filling and a cleaning would be an invention, not a measurement.
    """
    from app.repositories.analytics import profitability
    from app.repositories.filters import Filters

    t = (await profitability(db, Filters()))["totals"]

    assert t["gross_margin"] == 510            # 540 + (-30)
    assert t["operating_margin"] < t["gross_margin"]
    assert t["operating_margin"] == t["gross_margin"] - t["payroll"]
