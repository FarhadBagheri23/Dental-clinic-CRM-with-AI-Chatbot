from datetime import datetime
from typing import Annotated

from fastapi import APIRouter, Depends, Query

from app.api.deps import CurrentUser, Database
from app.core.redaction import COMMISSION, PATIENT_CONTACT, is_owner, scrub
from app.repositories import analytics as repo
from app.repositories.filters import Filters

router = APIRouter(prefix="/analytics", tags=["analytics"])


def filter_params(
    date_from: datetime | None = Query(None, description="ISO date, inclusive"),
    date_to: datetime | None = Query(None, description="ISO date, inclusive"),
    specialty: str | None = Query(None, max_length=64),
    category: str | None = Query(None, max_length=64),
    insurance: str | None = Query(None, max_length=64),
) -> Filters:
    """Global dashboard filters (report §۷). Declared once and shared by every
    analytics endpoint so a new filter is added in one place."""
    return Filters(
        date_from=date_from,
        date_to=date_to,
        specialty=specialty or None,
        category=category or None,
        insurance=insurance or None,
    )


Filter = Annotated[Filters, Depends(filter_params)]


@router.get("/filters")
async def filter_options(db: Database, user: CurrentUser) -> dict:
    """Values the client should offer in the filter bar."""
    return await repo.get_filter_options(db)


# ------------------------------------------- page 2 — revenue & services

@router.get("/revenue-by-category")
async def revenue_by_category(db: Database, user: CurrentUser, f: Filter) -> list[dict]:
    return await repo.revenue_by_category(db, f)


@router.get("/service-mix")
async def service_mix(
    db: Database, user: CurrentUser, f: Filter, limit: int = Query(10, ge=1, le=25)
) -> list[dict]:
    return await repo.service_mix(db, f, limit)


# --------------------------------------------------- page 3 — dentists

@router.get("/dentists")
async def dentists(db: Database, user: CurrentUser, f: Filter) -> list[dict]:
    rows = await repo.dentist_scorecard(db, f)
    return rows if is_owner(user) else scrub(rows, COMMISSION)


# ------------------------------------------------- page 4 — operations

@router.get("/appointment-trend")
async def appointment_trend(db: Database, user: CurrentUser, f: Filter) -> list[dict]:
    return await repo.appointment_trend(db, f)


@router.get("/heatmap")
async def heatmap(db: Database, user: CurrentUser, f: Filter) -> list[dict]:
    return await repo.hourly_heatmap(db, f)


@router.get("/chairs")
async def chairs(db: Database, user: CurrentUser, f: Filter) -> dict:
    return await repo.chair_utilisation(db, f)


# ---------------------------------------------- page 5 — finance & stock

@router.get("/receivables")
async def receivables(db: Database, user: CurrentUser, f: Filter) -> dict:
    return await repo.receivables(db, f)


@router.get("/payment-methods")
async def payment_methods(db: Database, user: CurrentUser, f: Filter) -> list[dict]:
    return await repo.payment_methods(db, f)


@router.get("/consumable-cost")
async def consumable_cost(db: Database, user: CurrentUser, f: Filter) -> list[dict]:
    return await repo.consumable_cost_by_category(db, f)


@router.get("/patients")
async def patients(db: Database, user: CurrentUser, f: Filter) -> dict:
    return await repo.patient_insights(db, f)


@router.get("/kpis")
async def kpis(db: Database, user: CurrentUser, f: Filter) -> list[dict]:
    """Monthly series for every headline KPI — value, delta and sparkline."""
    return await repo.monthly_kpis(db, f)


# ---------------------------------------------- clinical (dentist view)

@router.get("/treatment-plans")
async def treatment_plans(db: Database, user: CurrentUser, f: Filter) -> dict:
    """Case acceptance, plan delivery, and quoted-but-undone treatment."""
    data = await repo.treatment_plans(db, f)
    if not is_owner(user):
        # The totals stay: only the named call list is withheld.
        data["overdue_plans"] = scrub(data["overdue_plans"], PATIENT_CONTACT)
    return data


@router.get("/recall")
async def recall(db: Database, user: CurrentUser, f: Filter) -> dict:
    """Active vs. lapsed patients and the monthly new/returning split."""
    data = await repo.patient_recall(db, f)
    if not is_owner(user):
        data["recall_list"] = scrub(data["recall_list"], PATIENT_CONTACT)
    return data


@router.get("/lost-slots")
async def lost_slots(db: Database, user: CurrentUser, f: Filter) -> dict:
    """Cancellations and no-shows priced in tomans and chair-hours."""
    return await repo.lost_slot_cost(db, f)


# ------------------------------------------------ accounting (owner view)

@router.get("/aging")
async def aging(db: Database, user: CurrentUser, f: Filter) -> dict:
    """A/R ageing ladder, DSO, and average days to settle an invoice."""
    data = await repo.receivables_aging(db, f)
    if not is_owner(user):
        data["worst"] = scrub(data["worst"], PATIENT_CONTACT)
    return data


@router.get("/profitability")
async def profitability(db: Database, user: CurrentUser, f: Filter) -> dict:
    """Gross margin per service, discount leakage and payroll as a share of
    revenue — what is left after the cost of delivering the treatment."""
    return await repo.profitability(db, f)
