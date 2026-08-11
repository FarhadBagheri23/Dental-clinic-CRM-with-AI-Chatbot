"""Aggregation pipelines behind the dashboard.

Kept out of the router so the shape of a KPI can change without touching
HTTP concerns, and so the pipelines can be exercised directly in tests.
"""

import asyncio

from motor.motor_asyncio import AsyncIOMotorDatabase

# Status values are Persian in the source data.
STATUS_BOOKED = "رزرو"


async def _scalar(db: AsyncIOMotorDatabase, collection: str, field: str) -> float:
    rows = await db[collection].aggregate(
        [{"$group": {"_id": None, "v": {"$sum": f"${field}"}}}]
    ).to_list(1)
    return rows[0]["v"] if rows else 0


async def _by_status(db: AsyncIOMotorDatabase, collection: str) -> list[dict]:
    rows = await db[collection].aggregate([
        {"$group": {"_id": "$status", "n": {"$sum": 1}}},
        {"$sort": {"n": -1}},
    ]).to_list(None)
    return [{"status": r["_id"], "n": r["n"]} for r in rows]


async def get_summary(db: AsyncIOMotorDatabase) -> dict:
    (
        revenue, covered, share, collected,
        appointment_status, invoice_status,
        patients, sessions, dentists, upcoming,
    ) = await asyncio.gather(
        _scalar(db, "invoices", "total_amount"),
        _scalar(db, "invoices", "insurance_covered"),
        _scalar(db, "invoices", "patient_share"),
        _scalar(db, "payments", "amount"),
        _by_status(db, "appointments"),
        _by_status(db, "invoices"),
        db.patients.count_documents({}),
        db.treatment_sessions.count_documents({}),
        db.dentists.count_documents({}),
        db.appointments.count_documents({"status": STATUS_BOOKED}),
    )

    return {
        "revenue": revenue,
        "insurance_covered": covered,
        "patient_share": share,
        "collected": collected,
        "outstanding": share - collected,
        # Collection rate measures against the patient's share, not total
        # revenue — the insurer's portion was never the patient's to pay.
        "collection_rate": round(collected / share * 100) if share else 0,
        "counts": {
            "patients": patients,
            "sessions": sessions,
            "dentists": dentists,
            "upcoming": upcoming,
            "appointments": sum(r["n"] for r in appointment_status),
        },
        "appointment_status": appointment_status,
        "invoice_status": invoice_status,
    }


async def get_revenue_trend(db: AsyncIOMotorDatabase, months: int = 12) -> list[dict]:
    """Revenue and collections per month, oldest first.

    Revenue is measured at the treatment session — when the work was actually
    delivered — not at the invoice issue date. Two reasons: every analytics
    page already defines revenue that way, so sourcing it differently here
    made the landing page disagree with the rest of the panel; and invoices
    in this dataset are all raised inside one narrow recent window, which
    collapsed a twelve-month trend into three bars.
    """
    billed = await db.treatment_sessions.aggregate([
        {"$group": {
            "_id": {"$dateToString": {"format": "%Y-%m", "date": "$session_date"}},
            "revenue": {"$sum": "$actual_cost"},
        }},
        {"$sort": {"_id": -1}}, {"$limit": months},
    ]).to_list(None)

    # Payments are matched to the months we actually selected. Limiting the
    # two pipelines independently lets them disagree on which months are in
    # the window, and a month present in one but not the other silently
    # reports zero collected.
    wanted = [r["_id"] for r in billed]
    paid = await db.payments.aggregate([
        {"$project": {
            "m": {"$dateToString": {"format": "%Y-%m", "date": "$payment_date"}},
            "amount": 1,
        }},
        {"$match": {"m": {"$in": wanted}}},
        {"$group": {"_id": "$m", "collected": {"$sum": "$amount"}}},
    ]).to_list(None)

    collected_by_month = {r["_id"]: r["collected"] for r in paid}
    return [
        {
            "month": r["_id"],
            "revenue": r["revenue"],
            "collected": collected_by_month.get(r["_id"], 0),
        }
        for r in sorted(billed, key=lambda r: r["_id"])
    ]


async def get_dentist_performance(db: AsyncIOMotorDatabase) -> list[dict]:
    """Revenue per dentist derived from sessions rather than invoices, so the
    figure stays correct when a treatment plan spans a reporting boundary."""
    return await db.treatment_sessions.aggregate([
        {"$lookup": {"from": "treatment_plans", "localField": "plan_id",
                     "foreignField": "plan_id", "as": "plan"}},
        {"$unwind": "$plan"},
        {"$group": {"_id": "$plan.dentist_id",
                    "revenue": {"$sum": "$actual_cost"},
                    "sessions": {"$sum": 1}}},
        {"$lookup": {"from": "dentists", "localField": "_id",
                     "foreignField": "dentist_id", "as": "d"}},
        {"$unwind": "$d"},
        {"$project": {
            "_id": 0,
            "name": {"$concat": ["دکتر ", "$d.first_name", " ", "$d.last_name"]},
            "specialty": "$d.specialty",
            "revenue": 1, "sessions": 1,
        }},
        {"$sort": {"revenue": -1}},
    ]).to_list(None)


async def get_top_services(db: AsyncIOMotorDatabase, limit: int = 8) -> list[dict]:
    return await db.treatment_sessions.aggregate([
        {"$group": {"_id": "$service_id", "n": {"$sum": 1},
                    "revenue": {"$sum": "$actual_cost"}}},
        {"$lookup": {"from": "services", "localField": "_id",
                     "foreignField": "service_id", "as": "s"}},
        {"$unwind": "$s"},
        {"$project": {"_id": 0, "name": "$s.name", "category": "$s.category",
                      "n": 1, "revenue": 1}},
        {"$sort": {"revenue": -1}},
        {"$limit": limit},
    ]).to_list(None)


async def get_low_stock(db: AsyncIOMotorDatabase) -> list[dict]:
    """Items at or below 1.5x their reorder point — `critical` marks the ones
    already under it."""
    return await db.consumables.aggregate([
        {"$match": {"$expr": {"$lte": ["$stock_quantity",
                                       {"$multiply": ["$min_stock_level", 1.5]}]}}},
        {"$addFields": {"critical": {"$lte": ["$stock_quantity", "$min_stock_level"]}}},
        {"$project": {"_id": 0}},
        {"$sort": {"critical": -1, "stock_quantity": 1}},
    ]).to_list(None)
