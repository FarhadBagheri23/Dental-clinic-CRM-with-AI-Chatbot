from fastapi import APIRouter, Query

from app.api.deps import CurrentUser, Database
from app.repositories import dashboard as repo
from app.schemas.dashboard import (
    ConsumableStock,
    DentistPerformance,
    MonthlyRevenue,
    ServiceRevenue,
    Summary,
)

# Every route in this group requires a session; declaring the dependency on
# the router means a new endpoint added here is protected by default.
router = APIRouter(prefix="/dashboard", tags=["dashboard"])


@router.get("", response_model=Summary)
async def summary(db: Database, user: CurrentUser) -> dict:
    return await repo.get_summary(db)


@router.get("/revenue-trend", response_model=list[MonthlyRevenue])
async def revenue_trend(
    db: Database, user: CurrentUser, months: int = Query(12, ge=1, le=36)
) -> list[dict]:
    return await repo.get_revenue_trend(db, months)


@router.get("/dentists", response_model=list[DentistPerformance])
async def dentists(db: Database, user: CurrentUser) -> list[dict]:
    return await repo.get_dentist_performance(db)


@router.get("/services", response_model=list[ServiceRevenue])
async def services(
    db: Database, user: CurrentUser, limit: int = Query(8, ge=1, le=25)
) -> list[dict]:
    return await repo.get_top_services(db, limit)


@router.get("/inventory", response_model=list[ConsumableStock])
async def inventory(db: Database, user: CurrentUser) -> list[dict]:
    return await repo.get_low_stock(db)
