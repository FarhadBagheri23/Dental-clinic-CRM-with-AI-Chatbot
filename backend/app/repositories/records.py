"""Paged, joined list queries for the records pages."""

import re

from motor.motor_asyncio import AsyncIOMotorDatabase

PAGE_SIZE = 20

FULL_NAME = {"$concat": [{"$first": "$p.first_name"}, " ", {"$first": "$p.last_name"}]}
DENTIST_NAME = {"$concat": ["دکتر ", {"$first": "$d.first_name"}, " ", {"$first": "$d.last_name"}]}


def _page_meta(total: int, page: int) -> dict:
    pages = max(-(-total // PAGE_SIZE), 1)
    return {"total": total, "page": min(page, pages), "pages": pages, "size": PAGE_SIZE}


async def _paged(db, collection, filter_, sort, stages, page):
    total = await db[collection].count_documents(filter_)
    meta = _page_meta(total, page)
    rows = await db[collection].aggregate([
        {"$match": filter_},
        {"$sort": sort},
        {"$skip": (meta["page"] - 1) * PAGE_SIZE},
        {"$limit": PAGE_SIZE},
        *stages,
    ]).to_list(None)
    return {"rows": rows, "meta": meta}


def _search_filter(q: str) -> dict:
    if not q:
        return {}
    # Escaped so a user typing "." or "(" searches for that character rather
    # than injecting a regex that scans the whole collection.
    safe = re.escape(q)
    digits = re.sub(r"\D", "", q)
    clauses = [
        {"first_name": {"$regex": safe, "$options": "i"}},
        {"last_name": {"$regex": safe, "$options": "i"}},
    ]
    if digits:
        clauses += [
            {"national_code": {"$regex": f"^{digits}"}},
            {"phone": {"$regex": digits}},
        ]
    return {"$or": clauses}


async def list_patients(db: AsyncIOMotorDatabase, q: str = "", page: int = 1) -> dict:
    return await _paged(
        db, "patients", _search_filter(q), {"patient_id": -1},
        [
            {"$lookup": {"from": "insurance", "localField": "insurance_id",
                         "foreignField": "insurance_id", "as": "ins"}},
            # `allergies` and `birth_date` were selected here but rendered by
            # nothing. Allergies are health data and a birth date is a strong
            # identifier, so the list stops shipping them rather than leaving
            # them in a payload anyone can read from the network tab.
            {"$project": {
                "_id": 0, "patient_id": 1, "national_code": 1, "first_name": 1,
                "last_name": 1, "gender": 1, "phone": 1,
                "registration_date": 1,
                "insurance": {"$ifNull": [{"$first": "$ins.company_name"}, None]},
            }},
        ],
        page,
    )


async def list_appointments(db: AsyncIOMotorDatabase, status: str = "", page: int = 1) -> dict:
    return await _paged(
        db, "appointments", {"status": status} if status else {},
        {"scheduled_datetime": -1},
        [
            {"$lookup": {"from": "patients", "localField": "patient_id",
                         "foreignField": "patient_id", "as": "p"}},
            {"$lookup": {"from": "dentists", "localField": "dentist_id",
                         "foreignField": "dentist_id", "as": "d"}},
            {"$project": {
                "_id": 0, "appointment_id": 1, "scheduled_datetime": 1,
                "status": 1, "chair_number": 1,
                "patient": FULL_NAME, "dentist": DENTIST_NAME,
                "specialty": {"$first": "$d.specialty"},
            }},
        ],
        page,
    )


async def list_invoices(db: AsyncIOMotorDatabase, status: str = "", page: int = 1) -> dict:
    return await _paged(
        db, "invoices", {"status": status} if status else {}, {"issue_date": -1},
        [
            {"$lookup": {"from": "patients", "localField": "patient_id",
                         "foreignField": "patient_id", "as": "p"}},
            {"$lookup": {"from": "payments", "localField": "invoice_id",
                         "foreignField": "invoice_id", "as": "pay"}},
            {"$project": {
                "_id": 0, "invoice_id": 1, "issue_date": 1, "total_amount": 1,
                "insurance_covered": 1, "patient_share": 1, "status": 1,
                "patient": FULL_NAME, "paid": {"$sum": "$pay.amount"},
            }},
            {"$addFields": {"balance": {"$subtract": ["$patient_share", "$paid"]}}},
        ],
        page,
    )
