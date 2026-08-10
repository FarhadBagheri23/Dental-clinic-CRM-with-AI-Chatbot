"""Analytical pipelines for dashboard pages 2–5 (report §۷).

Metric choices follow ANALYSIS_full.md §10: services rank by revenue per
chair-hour rather than gross revenue, and dentists carry margin alongside
revenue so the commission inversion is visible.
"""

import asyncio

from motor.motor_asyncio import AsyncIOMotorDatabase

from app.repositories.filters import Filters, session_pipeline

# The clinic runs 6 chairs, 08:00–20:00, closed Friday (ANALYSIS_full.md).
CHAIRS = 6
OPEN_HOUR, CLOSE_HOUR = 8, 20
WORKING_DAYS_PER_WEEK = 6

STATUS_DONE = "انجام‌شده"
STATUS_CANCELLED = "لغو"
STATUS_NOSHOW = "غایب"


# --------------------------------------------------------------- filters

async def get_filter_options(db: AsyncIOMotorDatabase) -> dict:
    specialties, categories, insurers, bounds = await asyncio.gather(
        db.dentists.distinct("specialty"),
        db.services.distinct("category"),
        db.insurance.distinct("company_name"),
        db.treatment_sessions.aggregate([
            {"$group": {"_id": None, "min": {"$min": "$session_date"},
                        "max": {"$max": "$session_date"}}},
        ]).to_list(1),
    )
    span = bounds[0] if bounds else {}
    return {
        "specialties": sorted(specialties),
        "categories": sorted(categories),
        "insurers": sorted(insurers),
        "date_min": span.get("min"),
        "date_max": span.get("max"),
    }


# ------------------------------------------- page 2 — revenue & services

async def revenue_by_category(db, f: Filters) -> list[dict]:
    return await db.treatment_sessions.aggregate([
        *session_pipeline(f, need_service=True),
        {"$group": {"_id": "$service.category",
                    "revenue": {"$sum": "$actual_cost"},
                    "sessions": {"$sum": 1}}},
        {"$project": {"_id": 0, "category": "$_id", "revenue": 1, "sessions": 1}},
        {"$sort": {"revenue": -1}},
    ]).to_list(None)


async def service_mix(db, f: Filters, limit: int = 10) -> list[dict]:
    """Top services with revenue per chair-hour.

    Ranking by gross revenue makes a high-volume cheap service look like the
    star; dividing by the chair time it consumes shows what actually earns.
    """
    return await db.treatment_sessions.aggregate([
        *session_pipeline(f, need_service=True),
        {"$group": {
            "_id": "$service.service_id",
            "name": {"$first": "$service.name"},
            "category": {"$first": "$service.category"},
            "duration": {"$first": "$service.duration_minutes"},
            "revenue": {"$sum": "$actual_cost"},
            "sessions": {"$sum": 1},
        }},
        {"$addFields": {
            "avg_ticket": {"$divide": ["$revenue", "$sessions"]},
            "chair_hours": {"$divide": [{"$multiply": ["$sessions", "$duration"]}, 60]},
        }},
        {"$addFields": {
            "revenue_per_hour": {
                "$cond": [{"$gt": ["$chair_hours", 0]},
                          {"$divide": ["$revenue", "$chair_hours"]}, 0],
            },
        }},
        {"$project": {"_id": 0, "duration": 0}},
        {"$sort": {"revenue": -1}},
        {"$limit": limit},
    ]).to_list(None)


# --------------------------------------------------- page 3 — dentists

async def dentist_scorecard(db, f: Filters) -> list[dict]:
    """Revenue, sessions, commission and clinic margin per dentist.

    Margin matters because commission_rate varies 25–45%: the top earner by
    revenue is not always the top contributor to the clinic.
    """
    revenue = await db.treatment_sessions.aggregate([
        *session_pipeline(f, need_dentist=True),
        {"$group": {
            "_id": "$dentist.dentist_id",
            "first_name": {"$first": "$dentist.first_name"},
            "last_name": {"$first": "$dentist.last_name"},
            "specialty": {"$first": "$dentist.specialty"},
            "commission_rate": {"$first": "$dentist.commission_rate"},
            "revenue": {"$sum": "$actual_cost"},
            "sessions": {"$sum": 1},
            "patients": {"$addToSet": "$plan.patient_id"},
        }},
        {"$addFields": {
            # Carried out of _id so the reliability merge below can key on it.
            "dentist_id": "$_id",
            "name": {"$concat": ["دکتر ", "$first_name", " ", "$last_name"]},
            "patients": {"$size": "$patients"},
            "commission": {"$multiply": ["$revenue", {"$divide": ["$commission_rate", 100]}]},
        }},
        {"$addFields": {"margin": {"$subtract": ["$revenue", "$commission"]}}},
        {"$project": {"_id": 0, "first_name": 0, "last_name": 0}},
        {"$sort": {"revenue": -1}},
    ]).to_list(None)

    # Reliability comes from appointments, which have no plan/service link.
    reliability = await db.appointments.aggregate([
        *([{"$match": f.date_match("scheduled_datetime")}]
          if f.date_match("scheduled_datetime") else []),
        {"$group": {
            "_id": "$dentist_id",
            "total": {"$sum": 1},
            "cancelled": {"$sum": {"$cond": [{"$eq": ["$status", STATUS_CANCELLED]}, 1, 0]}},
            "noshow": {"$sum": {"$cond": [{"$eq": ["$status", STATUS_NOSHOW]}, 1, 0]}},
        }},
    ]).to_list(None)
    rates = {
        r["_id"]: {
            "cancel_rate": round(r["cancelled"] / r["total"] * 100, 1) if r["total"] else 0,
            "noshow_rate": round(r["noshow"] / r["total"] * 100, 1) if r["total"] else 0,
        }
        for r in reliability
    }

    for row in revenue:
        row.update(rates.get(row["dentist_id"], {"cancel_rate": 0, "noshow_rate": 0}))
    return revenue


# ------------------------------------------------- page 4 — operations

async def appointment_trend(db, f: Filters) -> list[dict]:
    """Completion / cancellation / no-show share per month."""
    rows = await db.appointments.aggregate([
        *([{"$match": f.date_match("scheduled_datetime")}]
          if f.date_match("scheduled_datetime") else []),
        {"$group": {
            "_id": {"$dateToString": {"format": "%Y-%m", "date": "$scheduled_datetime"}},
            "total": {"$sum": 1},
            "done": {"$sum": {"$cond": [{"$eq": ["$status", STATUS_DONE]}, 1, 0]}},
            "cancelled": {"$sum": {"$cond": [{"$eq": ["$status", STATUS_CANCELLED]}, 1, 0]}},
            "noshow": {"$sum": {"$cond": [{"$eq": ["$status", STATUS_NOSHOW]}, 1, 0]}},
        }},
        {"$sort": {"_id": 1}},
    ]).to_list(None)

    return [
        {
            "month": r["_id"], "total": r["total"], "done": r["done"],
            "cancelled": r["cancelled"], "noshow": r["noshow"],
            "cancel_rate": round(r["cancelled"] / r["total"] * 100, 1),
            "noshow_rate": round(r["noshow"] / r["total"] * 100, 1),
            # Lost slots are the operational headline: each one is chair time
            # that was reserved and produced nothing.
            "lost_rate": round((r["cancelled"] + r["noshow"]) / r["total"] * 100, 1),
        }
        for r in rows if r["total"]
    ]


async def hourly_heatmap(db, f: Filters) -> list[dict]:
    """Appointment density by weekday × hour.

    $dayOfWeek returns 1=Sunday; Persian weeks start Saturday, so the client
    is given the raw index and does the naming.
    """
    return await db.appointments.aggregate([
        *([{"$match": f.date_match("scheduled_datetime")}]
          if f.date_match("scheduled_datetime") else []),
        {"$group": {
            "_id": {
                "dow": {"$dayOfWeek": "$scheduled_datetime"},
                "hour": {"$hour": "$scheduled_datetime"},
            },
            "n": {"$sum": 1},
        }},
        {"$project": {"_id": 0, "dow": "$_id.dow", "hour": "$_id.hour", "n": 1}},
        {"$sort": {"dow": 1, "hour": 1}},
    ]).to_list(None)


async def chair_utilisation(db, f: Filters) -> dict:
    """Booked chair-hours against capacity.

    Utilisation runs near 10% in this dataset. That is the finding, not a
    rendering fault — ANALYSIS_full.md §10 asks for it to be labelled.
    """
    rows = await db.appointments.aggregate([
        *([{"$match": f.date_match("scheduled_datetime")}]
          if f.date_match("scheduled_datetime") else []),
        {"$group": {
            "_id": "$chair_number",
            "total": {"$sum": 1},
            "done": {"$sum": {"$cond": [{"$eq": ["$status", STATUS_DONE]}, 1, 0]}},
        }},
        {"$project": {"_id": 0, "chair": "$_id", "total": 1, "done": 1}},
        {"$sort": {"chair": 1}},
    ]).to_list(None)

    span = await db.appointments.aggregate([
        {"$group": {"_id": None, "min": {"$min": "$scheduled_datetime"},
                    "max": {"$max": "$scheduled_datetime"}}},
    ]).to_list(1)

    weeks = 0.0
    if span and span[0].get("min") and span[0].get("max"):
        weeks = (span[0]["max"] - span[0]["min"]).days / 7

    # One appointment ≈ one 30-minute slot.
    slots_per_chair = weeks * WORKING_DAYS_PER_WEEK * (CLOSE_HOUR - OPEN_HOUR) * 2
    for r in rows:
        r["utilisation"] = round(r["total"] / slots_per_chair * 100, 1) if slots_per_chair else 0

    booked = sum(r["total"] for r in rows)
    capacity = slots_per_chair * CHAIRS
    return {
        "chairs": rows,
        "overall_utilisation": round(booked / capacity * 100, 1) if capacity else 0,
        "capacity_slots": round(capacity),
        "booked_slots": booked,
        # Utilisation is only meaningful next to the capacity model used to
        # compute it. Returned so the UI can state the assumption instead of
        # presenting a bare percentage the viewer cannot check.
        "assumptions": {
            "chairs": CHAIRS,
            "open_hour": OPEN_HOUR,
            "close_hour": CLOSE_HOUR,
            "working_days_per_week": WORKING_DAYS_PER_WEEK,
            "slot_minutes": 30,
            "weeks_in_window": round(weeks, 1),
        },
    }


# ------------------------------------------ page 5 — finance & stock

async def receivables(db, f: Filters) -> dict:
    """The billed → insurance → patient share → collected → outstanding chain."""
    date = f.date_match("issue_date")
    totals = await db.invoices.aggregate([
        *([{"$match": date}] if date else []),
        {"$group": {"_id": None,
                    "billed": {"$sum": "$total_amount"},
                    "insurance": {"$sum": "$insurance_covered"},
                    "patient_share": {"$sum": "$patient_share"}}},
    ]).to_list(1)
    paid = await db.payments.aggregate([
        *([{"$match": f.date_match("payment_date")}] if f.date_match("payment_date") else []),
        {"$group": {"_id": None, "collected": {"$sum": "$amount"}}},
    ]).to_list(1)

    t = totals[0] if totals else {"billed": 0, "insurance": 0, "patient_share": 0}
    collected = paid[0]["collected"] if paid else 0
    by_status = await db.invoices.aggregate([
        *([{"$match": date}] if date else []),
        {"$group": {"_id": "$status", "n": {"$sum": 1},
                    "amount": {"$sum": "$patient_share"}}},
        {"$project": {"_id": 0, "status": "$_id", "n": 1, "amount": 1}},
        {"$sort": {"amount": -1}},
    ]).to_list(None)

    return {
        "billed": t["billed"],
        "insurance": t["insurance"],
        "patient_share": t["patient_share"],
        "collected": collected,
        "outstanding": t["patient_share"] - collected,
        "by_status": by_status,
    }


async def payment_methods(db, f: Filters) -> list[dict]:
    date = f.date_match("payment_date")
    return await db.payments.aggregate([
        *([{"$match": date}] if date else []),
        {"$group": {"_id": "$method", "amount": {"$sum": "$amount"}, "n": {"$sum": 1}}},
        {"$project": {"_id": 0, "method": "$_id", "amount": 1, "n": 1}},
        {"$sort": {"amount": -1}},
    ]).to_list(None)


async def consumable_cost_by_category(db, f: Filters) -> list[dict]:
    """Material cost per service category — the input side of margin."""
    return await db.consumable_usage.aggregate([
        *([{"$match": f.date_match("usage_date")}] if f.date_match("usage_date") else []),
        {"$lookup": {"from": "consumables", "localField": "consumable_id",
                     "foreignField": "consumable_id", "as": "c"}},
        {"$unwind": "$c"},
        {"$lookup": {"from": "treatment_sessions", "localField": "session_id",
                     "foreignField": "session_id", "as": "s"}},
        {"$unwind": "$s"},
        {"$lookup": {"from": "services", "localField": "s.service_id",
                     "foreignField": "service_id", "as": "svc"}},
        {"$unwind": "$svc"},
        *([{"$match": {"svc.category": f.category}}] if f.category else []),
        {"$group": {
            "_id": "$svc.category",
            "cost": {"$sum": {"$multiply": ["$quantity_used", "$c.unit_price"]}},
            "revenue": {"$sum": "$s.actual_cost"},
        }},
        {"$project": {"_id": 0, "category": "$_id", "cost": 1, "revenue": 1}},
        {"$sort": {"cost": -1}},
    ]).to_list(None)


async def patient_insights(db, f: Filters) -> dict:
    """Concentration and insurance mix — who the revenue actually comes from."""
    per_patient = await db.treatment_sessions.aggregate([
        *session_pipeline(f, need_patient=True),
        {"$group": {"_id": "$plan.patient_id", "revenue": {"$sum": "$actual_cost"}}},
        {"$sort": {"revenue": -1}},
    ]).to_list(None)

    total = sum(p["revenue"] for p in per_patient) or 1
    top_decile = per_patient[: max(1, len(per_patient) // 10)]

    by_insurer = await db.patients.aggregate([
        {"$lookup": {"from": "insurance", "localField": "insurance_id",
                     "foreignField": "insurance_id", "as": "i"}},
        {"$group": {
            "_id": {"$ifNull": [{"$first": "$i.company_name"}, "آزاد"]},
            "n": {"$sum": 1},
        }},
        {"$project": {"_id": 0, "insurer": "$_id", "n": 1}},
        {"$sort": {"n": -1}},
    ]).to_list(None)

    return {
        "treated_patients": len(per_patient),
        "top_decile_share": round(sum(p["revenue"] for p in top_decile) / total * 100, 1),
        "avg_revenue_per_patient": round(total / len(per_patient)) if per_patient else 0,
        "by_insurer": by_insurer,
    }
