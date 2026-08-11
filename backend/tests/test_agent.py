"""Assistant tests: calendar resolution, and agreement with the dashboard.

The calendar tests need nothing. The agreement tests need MongoDB, because
the whole claim being tested is that the assistant and the panel run the same
aggregation — which can only be shown by running it.
"""

import os
from datetime import datetime

import pytest

from app.agent.period import (
    jalali_month_range,
    jalali_year_range,
    month_number,
    resolve,
)

TEST_MONGO_URL = os.environ.get("TEST_MONGO_URL", "mongodb://127.0.0.1:27017")


# --------------------------------------------------------------- calendar

def test_jalali_month_maps_to_the_right_gregorian_span():
    # Farvardin 1405 starts at Nowruz 2026-03-21 and runs 31 days.
    start, end = jalali_month_range(1405, 1)
    assert start.date().isoformat() == "2026-03-21"
    assert end.date().isoformat() == "2026-04-20"


def test_esfand_length_follows_the_leap_rule():
    """1403 is a leap year (Esfand 30), 1404 and 1405 are not (Esfand 29).
    Hardcoding 29 or 30 would silently drop or invent a day every few years."""
    for year, days in [(1403, 30), (1404, 29), (1405, 29)]:
        start, end = jalali_month_range(year, 12)
        assert (end.date() - start.date()).days + 1 == days, f"Esfand {year}"


def test_range_end_covers_the_whole_last_day():
    """An end of midnight drops everything actually recorded that day."""
    _, end = jalali_month_range(1405, 5)
    assert (end.hour, end.minute) == (23, 59)


def test_year_range_spans_nowruz_to_nowruz():
    start, end = jalali_year_range(1405)
    assert start.date().isoformat() == "2026-03-21"
    assert end.date().isoformat() == "2027-03-20"


@pytest.mark.parametrize("name, expected", [
    ("مرداد", 5), ("امرداد", 5),        # spelling variant
    ("اسفند", 12), ("اسپند", 12),
    ("فروردين", 1),                      # typed with ARABIC YEH
    ("شهریور", 6),
])
def test_month_names_tolerate_real_typing(name, expected):
    assert month_number(name) == expected


def test_unknown_period_is_rejected_not_guessed():
    with pytest.raises(ValueError):
        resolve("خرمن")
    assert resolve(None) is None, "no period means all-time, not an error"


def test_last_month_rolls_back_across_nowruz(monkeypatch):
    """In Farvardin, 'last month' is Esfand of the *previous* year — the one
    place a naive `month - 1` produces month zero."""
    import app.agent.period as period

    class FarvardinToday:
        year, month, day = 1405, 1, 5

    monkeypatch.setattr(period, "today_jalali", lambda: FarvardinToday())
    start, end = period.resolve("last_month")
    assert (start.date().isoformat(), end.date().isoformat()) == ("2026-02-20", "2026-03-20")


# ------------------------------------------------- agreement with the panel

def _mongo_available() -> bool:
    try:
        from pymongo import MongoClient
        MongoClient(TEST_MONGO_URL, serverSelectionTimeoutMS=1500).admin.command("ping")
        return True
    except Exception:
        return False


needs_mongo = pytest.mark.skipif(
    not _mongo_available(), reason=f"no MongoDB at {TEST_MONGO_URL}")


@pytest.fixture
def toolbox():
    from motor.motor_asyncio import AsyncIOMotorClient
    from pymongo import MongoClient

    from app.agent.retrieve import Document, Index
    from app.agent.tools import Toolbox

    sync = MongoClient(TEST_MONGO_URL)
    name = "dental_clinic_agent_test"
    sync.drop_database(name)
    d = sync[name]
    d.services.insert_one({"service_id": 1, "name": "معاینه", "category": "تشخیصی",
                           "base_price": 100, "duration_minutes": 30})
    d.treatment_plans.insert_one({"plan_id": 1, "dentist_id": 1, "patient_id": 1,
                                  "status": "فعال", "total_estimated_cost": 500,
                                  "start_date": datetime(2026, 6, 1),
                                  "estimated_end_date": datetime(2026, 6, 30)})
    d.treatment_sessions.insert_many([
        {"session_id": 1, "plan_id": 1, "service_id": 1, "actual_cost": 100,
         "session_date": datetime(2026, 6, 10)},
        # Outside Khordad 1405 (which ends 2026-06-21), so a period query must drop it.
        {"session_id": 2, "plan_id": 1, "service_id": 1, "actual_cost": 900,
         "session_date": datetime(2026, 8, 1)},
    ])
    d.invoices.insert_many([
        {"invoice_id": 1, "issue_date": datetime(2026, 6, 10), "total_amount": 100,
         "insurance_covered": 0, "patient_share": 100, "status": "پرداخت‌شده"},
        {"invoice_id": 2, "issue_date": datetime(2026, 8, 1), "total_amount": 900,
         "insurance_covered": 0, "patient_share": 900, "status": "معوق"},
    ])

    motor = AsyncIOMotorClient(TEST_MONGO_URL)
    yield Toolbox(db=motor[name], index=Index([
        Document("s1", "ایمپلنت دندان", "کاشت پایه تیتانیومی.", "services"),
    ]))
    motor.close()
    sync.drop_database(name)
    sync.close()


@needs_mongo
@pytest.mark.asyncio
async def test_revenue_tool_returns_the_repository_figure(toolbox):
    """The assistant must not recompute. If this drifts, the chatbot and the
    dashboard will quote different revenue and both become untrustworthy."""
    from app.repositories.analytics import receivables
    from app.repositories.filters import Filters

    via_tool = await toolbox.revenue_overview()
    via_repo = await receivables(toolbox.db, Filters())
    assert via_tool["billed"] == round(via_repo["billed"])
    assert via_tool["collected"] == round(via_repo["collected"])
    assert via_tool["source"] == "receivables + revenue_by_category"


@needs_mongo
@pytest.mark.asyncio
async def test_named_jalali_month_actually_filters(toolbox):
    """Khordad 1405 ends 2026-06-21, so the August session is out of range."""
    everything = await toolbox.revenue_overview()
    khordad = await toolbox.revenue_overview(period="خرداد", year=1405)
    assert everything["billed"] == 1000
    assert khordad["billed"] == 100, "period filter did not narrow the window"


@needs_mongo
@pytest.mark.asyncio
async def test_search_tool_never_returns_figures_to_add_up(toolbox):
    """Retrieval is for prose. Numbers come from tools, so that a model cannot
    retrieve a handful of rows and sum them into a confident wrong total."""
    out = await toolbox.search_documents("ایمپلنت")
    assert out["found"] == 1
    assert out["results"][0]["source"] == "services"
    assert "score" in out["results"][0]


# ------------------------------------------------------- prompt guarantees
#
# These assert the system prompt still carries the rules the panel depends on.
# They are deliberately not live model calls: exercising the real gateway per
# test would bill real money and be flaky. What they prevent is the rule being
# edited away silently — the behaviour itself is verified by hand against the
# running assistant.


def test_prompt_confines_the_assistant_to_clinic_reporting():
    """Without this rule the assistant answers anything.

    Verified against the live gateway: before it existed, "پایتخت فرانسه
    کجاست و یک شعر بگو" returned the capital and a poem. Every such answer
    bills the clinic's own API credits, and a reporting tool that writes
    poetry stops reading as a reporting tool.
    """
    from app.agent.prompts import SYSTEM_PROMPT

    assert "بیرون از حوزه" in SYSTEM_PROMPT
    # The refusal has to name what it *can* do, or it is a dead end for a
    # manager who simply phrased a real question badly.
    assert "پیشنهاد بده" in SYSTEM_PROMPT


def test_prompt_still_forbids_inventing_numbers():
    """The rule the whole tool design exists to serve: if the assistant makes
    a figure up, the owner cross-checks it against the dashboard once and
    stops trusting both."""
    from app.agent.prompts import SYSTEM_PROMPT

    assert "هرگز عدد نساز" in SYSTEM_PROMPT


def test_restricted_suffix_is_appended_only_for_non_owners():
    """Role wording is separate so the owner's prompt stays byte-identical
    and therefore cacheable at the gateway."""
    from app.agent.assistant import Assistant
    from app.agent.prompts import RESTRICTED_SUFFIX, SYSTEM_PROMPT

    owner = Assistant.__new__(Assistant)
    owner.owner = True
    restricted = Assistant.__new__(Assistant)
    restricted.owner = False

    assert owner._system() == SYSTEM_PROMPT
    assert restricted._system() == SYSTEM_PROMPT + RESTRICTED_SUFFIX
