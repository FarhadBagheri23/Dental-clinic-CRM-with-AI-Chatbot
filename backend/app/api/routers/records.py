from fastapi import APIRouter, Query

from app.api.deps import CurrentUser, Database
from app.core.redaction import PATIENT_CONTACT, is_owner, scrub
from app.repositories import records as repo
from app.schemas.records import AppointmentPage, InvoicePage, PatientPage

router = APIRouter(tags=["records"])


@router.get("/patients", response_model=PatientPage)
async def patients(
    db: Database,
    user: CurrentUser,
    q: str = Query("", max_length=64),
    page: int = Query(1, ge=1),
) -> dict:
    data = await repo.list_patients(db, q.strip(), page)
    if not is_owner(user):
        # Search still works — a non-owner can confirm a patient exists
        # without the register becoming a downloadable contact list.
        data["rows"] = scrub(data["rows"], PATIENT_CONTACT)
    return data


@router.get("/appointments", response_model=AppointmentPage)
async def appointments(
    db: Database,
    user: CurrentUser,
    status: str = Query("", max_length=32),
    page: int = Query(1, ge=1),
) -> dict:
    return await repo.list_appointments(db, status, page)


@router.get("/invoices", response_model=InvoicePage)
async def invoices(
    db: Database,
    user: CurrentUser,
    status: str = Query("", max_length=32),
    page: int = Query(1, ge=1),
) -> dict:
    return await repo.list_invoices(db, status, page)
