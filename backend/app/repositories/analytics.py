"""Analytical pipelines for dashboard pages 2–5 (report §۷).

Metric choices follow ANALYSIS_full.md §10: services rank by revenue per
chair-hour rather than gross revenue, and dentists carry margin alongside
revenue so the commission inversion is visible.
"""

import asyncio
from dataclasses import replace
from datetime import UTC, datetime

from motor.motor_asyncio import AsyncIOMotorDatabase

from app.repositories.filters import (
    UNSUPPORTED_FILTERS,
    Filters,
    appointment_pipeline,
    invoice_pipeline,
    patient_pipeline,
    payment_pipeline,
    plan_pipeline,
    session_pipeline,
)

# The clinic runs 6 chairs, 08:00–20:00, closed Friday (ANALYSIS_full.md).
WORKING_DAYS_PER_WEEK = 6
SLOT_MINUTES = 30

STATUS_DONE = "انجام‌شده"
STATUS_CANCELLED = "لغو"
STATUS_NOSHOW = "غایب"

PLAN_ACTIVE = "فعال"
PLAN_DONE = "تکمیل‌شده"
PLAN_ON_HOLD = "معلق"
PLAN_CANCELLED = "لغو"

# A dental recall interval is six months — the point at which a patient with
# no visit stops being "active" and becomes someone reception should call.
RECALL_DAYS = 180


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
        # Which charts cannot honour which filter, so the UI can say so on the
        # affected card rather than presenting an unfiltered number as filtered.
        "unsupported": UNSUPPORTED_FILTERS,
    }


# ------------------------------------------- page 2 — revenue & services

async def revenue_by_category(db, f: Filters) -> list[dict]:
    return await db.treatment_sessions.aggregate([
        *session_pipeline(f, need_service=True),
        {"$group": {"_id": "$service.category",
                    "revenue": {"$sum": "$actual_cost"},
                    "sessions": {"$sum": 1}}},
        {"$project": {"_id": 0, "category": "$_id", "revenue": 1, "sessions": 1}},
        {"$sort": {"revenue": -1, "category": 1}},
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
        # need_service joins the service purely for `duration_minutes`, which
        # is what turns revenue into revenue per chair-hour below.
        *session_pipeline(f, need_dentist=True, need_service=True),
        {"$group": {
            "_id": "$dentist.dentist_id",
            "first_name": {"$first": "$dentist.first_name"},
            "last_name": {"$first": "$dentist.last_name"},
            "specialty": {"$first": "$dentist.specialty"},
            "commission_rate": {"$first": "$dentist.commission_rate"},
            "revenue": {"$sum": "$actual_cost"},
            "sessions": {"$sum": 1},
            "minutes": {"$sum": "$service.duration_minutes"},
            "patients": {"$addToSet": "$plan.patient_id"},
        }},
        {"$addFields": {
            # Carried out of _id so the reliability merge below can key on it.
            "dentist_id": "$_id",
            "name": {"$concat": ["دکتر ", "$first_name", " ", "$last_name"]},
            "patients": {"$size": "$patients"},
            "chair_hours": {"$divide": ["$minutes", 60]},
            "commission": {"$multiply": ["$revenue", {"$divide": ["$commission_rate", 100]}]},
        }},
        {"$addFields": {
            "margin": {"$subtract": ["$revenue", "$commission"]},
            # The fair comparison between dentists: ranking on gross revenue
            # rewards whoever was rostered the most chair time, while this
            # asks what each earned from the time they actually had.
            "revenue_per_hour": {"$cond": [
                {"$gt": ["$chair_hours", 0]},
                {"$divide": ["$revenue", "$chair_hours"]}, 0]},
        }},
        {"$project": {"_id": 0, "first_name": 0, "last_name": 0, "minutes": 0}},
        {"$sort": {"revenue": -1}},
    ]).to_list(None)

    # Reliability comes from appointments, which carry no service link, so a
    # category filter cannot reach them (see filters.py).
    reliability = await db.appointments.aggregate([
        *appointment_pipeline(f),
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
        *appointment_pipeline(f),
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
        *appointment_pipeline(f),
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
    """Chair time actually used, against the hours the clinic is staffed for.

    Both halves of this ratio are measured rather than assumed, which the
    earlier version did not do:

    * Numerator — real minutes. `TreatmentSession.appointment_id` is a 1:1
      link to the appointment (so: which chair) and `service_id` gives the
      service's `duration_minutes` (so: how long). Counting appointments and
      calling each one "a 30-minute slot" understated booked time by ~55%,
      because the average service runs 61 minutes and the spread is 15–120.
    * Denominator — staffed hours, from `clinic_capacity`. The chairs are not
      interchangeable: three are staffed 9h/day, one 7h, two only 4h. Treating
      capacity as `chairs x opening_hours` inflated it by ~70% by billing the
      clinic for chairs nobody was rostered on.
    """
    booked, capacity_rows, span = await asyncio.gather(
        db.treatment_sessions.aggregate([
            *session_pipeline(f, need_service=True),
            {"$lookup": {"from": "appointments", "localField": "appointment_id",
                         "foreignField": "appointment_id", "as": "appt"}},
            {"$unwind": "$appt"},
            {"$group": {"_id": "$appt.chair_number",
                        "minutes": {"$sum": "$service.duration_minutes"},
                        "sessions": {"$sum": 1}}},
            {"$project": {"_id": 0, "chair": "$_id", "minutes": 1, "sessions": 1}},
        ]).to_list(None),
        db.clinic_capacity.find({}, {"_id": 0}).sort("chair_number", 1).to_list(None),
        # Span comes from the sessions, which are the numerator. Taking it from
        # appointments instead stretched the denominator across bookings made
        # into the future, quietly deflating every chair's utilisation.
        db.treatment_sessions.aggregate([
            *session_pipeline(f),
            {"$group": {"_id": None, "min": {"$min": "$session_date"},
                        "max": {"$max": "$session_date"}}},
        ]).to_list(1),
    )

    if f.date_from and f.date_to:
        days = (f.date_to - f.date_from).days
    elif span and span[0].get("min") and span[0].get("max"):
        days = (span[0]["max"] - span[0]["min"]).days
    else:
        days = 0
    weeks = days / 7
    working_days = weeks * WORKING_DAYS_PER_WEEK

    booked_by_chair = {r["chair"]: r for r in booked}
    chairs = []
    for cap in capacity_rows:
        n = cap["chair_number"]
        used = booked_by_chair.get(n, {"minutes": 0, "sessions": 0})
        available_h = cap["staffed_hours_per_day"] * working_days
        used_h = used["minutes"] / 60
        chairs.append({
            "chair": n,
            "sessions": used["sessions"],
            "booked_hours": round(used_h, 1),
            "capacity_hours": round(available_h, 1),
            "staffed_hours_per_day": cap["staffed_hours_per_day"],
            "shift": f"{cap['start_hour']}–{cap['end_hour']}",
            "utilisation": round(used_h / available_h * 100, 1) if available_h else 0,
        })

    total_booked = sum(c["booked_hours"] for c in chairs)
    total_capacity = sum(c["capacity_hours"] for c in chairs)

    return {
        "chairs": chairs,
        "overall_utilisation": (
            round(total_booked / total_capacity * 100, 1) if total_capacity else 0
        ),
        "booked_hours": round(total_booked),
        "capacity_hours": round(total_capacity),
        # Utilisation is only meaningful next to the capacity model used to
        # compute it. Returned so the UI can state the assumption instead of
        # presenting a bare percentage the viewer cannot check.
        "assumptions": {
            "chairs": len(capacity_rows),
            "staffed_hours_per_day": sum(
                c["staffed_hours_per_day"] for c in capacity_rows),
            "working_days_per_week": WORKING_DAYS_PER_WEEK,
            "working_days_in_window": round(working_days),
            "weeks_in_window": round(weeks, 1),
            "source": "clinic_capacity",
        },
    }


# ------------------------------------------ page 5 — finance & stock

async def receivables(db, f: Filters) -> dict:
    """The billed → insurance → patient share → collected → outstanding chain."""
    totals, paid, cohort, by_status = await asyncio.gather(
        db.invoices.aggregate([
            *invoice_pipeline(f),
            {"$group": {"_id": None,
                        "billed": {"$sum": "$total_amount"},
                        "insurance": {"$sum": "$insurance_covered"},
                        "patient_share": {"$sum": "$patient_share"}}},
        ]).to_list(1),
        db.payments.aggregate([
            *payment_pipeline(f),
            {"$group": {"_id": None, "collected": {"$sum": "$amount"}}},
        ]).to_list(1),
        # Cash received in the window answers "what came in", but dividing it
        # by what was billed in the same window compares two different cohorts:
        # payments settle invoices raised earlier, so a filtered month can
        # report a collection rate over 100%. This figure matches payments to
        # the invoices actually issued in the window — "of what we billed, how
        # much have we been paid?". Driven from the invoice side so it reuses
        # invoice_pipeline and honours every filter the same way.
        db.invoices.aggregate([
            *invoice_pipeline(f),
            {"$lookup": {"from": "payments", "localField": "invoice_id",
                         "foreignField": "invoice_id", "as": "pay"}},
            {"$group": {"_id": None,
                        "collected": {"$sum": {"$sum": "$pay.amount"}}}},
        ]).to_list(1),
        db.invoices.aggregate([
            *invoice_pipeline(f),
            {"$group": {"_id": "$status", "n": {"$sum": 1},
                        "amount": {"$sum": "$patient_share"}}},
            {"$project": {"_id": 0, "status": "$_id", "n": 1, "amount": 1}},
            {"$sort": {"amount": -1, "status": 1}},
        ]).to_list(None),
    )

    t = totals[0] if totals else {"billed": 0, "insurance": 0, "patient_share": 0}
    collected = paid[0]["collected"] if paid else 0
    collected_on_window_invoices = cohort[0]["collected"] if cohort else 0

    return {
        "billed": t["billed"],
        "insurance": t["insurance"],
        "patient_share": t["patient_share"],
        # Cash that arrived during the window, whenever it was billed.
        "collected": collected,
        # Cash received against invoices issued during the window.
        "collected_on_window_invoices": collected_on_window_invoices,
        "outstanding": t["patient_share"] - collected_on_window_invoices,
        "collection_rate": (
            round(collected_on_window_invoices / t["patient_share"] * 100, 1)
            if t["patient_share"] else 0
        ),
        "by_status": by_status,
    }


async def payment_methods(db, f: Filters) -> list[dict]:
    return await db.payments.aggregate([
        *payment_pipeline(f),
        {"$group": {"_id": "$method", "amount": {"$sum": "$amount"}, "n": {"$sum": 1}}},
        {"$project": {"_id": 0, "method": "$_id", "amount": 1, "n": 1}},
        {"$sort": {"amount": -1, "method": 1}},
    ]).to_list(None)


async def consumable_cost_by_category(db, f: Filters) -> list[dict]:
    """Material cost per service category — the input side of margin.

    Rooted at the session rather than the usage row for two reasons. It shares
    `session_pipeline`, so specialty and insurer narrow it like every other
    page instead of only date and category. And it collapses back to one row
    per session before summing revenue: a session consuming three materials
    produces three usage rows, and summing `actual_cost` across them counted
    that session's revenue three times, understating material cost as a share
    of revenue on exactly the categories that use the most material.
    """
    return await db.treatment_sessions.aggregate([
        *session_pipeline(f, need_service=True),
        {"$lookup": {"from": "consumable_usage", "localField": "session_id",
                     "foreignField": "session_id", "as": "usage"}},
        {"$unwind": {"path": "$usage", "preserveNullAndEmptyArrays": True}},
        {"$lookup": {"from": "consumables", "localField": "usage.consumable_id",
                     "foreignField": "consumable_id", "as": "c"}},
        {"$unwind": {"path": "$c", "preserveNullAndEmptyArrays": True}},
        # Collapse back to one row per session before revenue is summed.
        {"$group": {"_id": "$session_id",
                    "category": {"$first": "$service.category"},
                    "revenue": {"$first": "$actual_cost"},
                    "cost": {"$sum": {"$multiply": [
                        {"$ifNull": ["$usage.quantity_used", 0]},
                        {"$ifNull": ["$c.unit_price", 0]}]}}}},
        {"$group": {"_id": "$category",
                    "cost": {"$sum": "$cost"},
                    "revenue": {"$sum": "$revenue"}}},
        {"$project": {"_id": 0, "category": "$_id", "cost": 1, "revenue": 1}},
        {"$sort": {"cost": -1, "category": 1}},
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


# ------------------------------------------------ clinical (dentist view)
#
# The three pipelines below answer what a dentist and a clinic manager
# actually run the practice on, and which revenue/appointment reporting
# alone cannot answer:
#
#   1. Of the treatment I diagnosed and quoted, how much got done?
#      (case acceptance and plan delivery — treatment_plans was unused)
#   2. Which patients have fallen out of recall and should be called?
#   3. What did the empty chairs cost, in tomans rather than percent?


async def treatment_plans(db, f: Filters) -> dict:
    """Case acceptance, plan completion, and the value quoted but not yet done.

    `unrealised` is the headline: treatment the patient already agreed to,
    sitting in open plans. It is the cheapest revenue in the clinic — no
    marketing needed, only a phone call — and it is invisible on every
    revenue chart because it has not been billed.
    """
    now = datetime.now(UTC)
    open_plans = {"status": {"$in": [PLAN_ACTIVE, PLAN_ON_HOLD]}}
    overdue_stages = [
        {"$match": {**open_plans, "estimated_end_date": {"$lt": now}}},
        {"$addFields": {"remaining": {"$max": [
            {"$subtract": ["$total_estimated_cost", "$delivered"]}, 0]}}},
    ]

    result = await db.treatment_plans.aggregate([
        *plan_pipeline(f),
        {"$facet": {
            "by_status": [
                {"$group": {"_id": "$status", "n": {"$sum": 1},
                            "planned": {"$sum": "$total_estimated_cost"},
                            "delivered": {"$sum": "$delivered"},
                            "sessions": {"$sum": "$sessions"}}},
                {"$project": {"_id": 0, "status": "$_id", "n": 1, "planned": 1,
                              "delivered": 1, "sessions": 1}},
                # Status breaks ties: two statuses with equal counts would
                # otherwise come back in whatever order the shard returned,
                # reordering the table between two identical refreshes.
                {"$sort": {"n": -1, "status": 1}},
            ],
            "open": [
                {"$match": open_plans},
                {"$group": {"_id": None,
                            "planned": {"$sum": "$total_estimated_cost"},
                            "delivered": {"$sum": "$delivered"}}},
            ],
            # Overdue is measured against the wall clock, not the filter
            # window: a plan that ran past its estimated end is late today
            # regardless of which months the user is looking at. Split across
            # two branches because $facet cannot nest.
            "overdue_total": [
                *overdue_stages,
                {"$group": {"_id": None, "n": {"$sum": 1},
                            "remaining": {"$sum": "$remaining"}}},
            ],
            "overdue_worst": [
                *overdue_stages,
                {"$sort": {"remaining": -1}},
                {"$limit": 10},
                {"$lookup": {"from": "patients", "localField": "patient_id",
                             "foreignField": "patient_id", "as": "p"}},
                {"$unwind": "$p"},
                {"$lookup": {"from": "dentists", "localField": "dentist_id",
                             "foreignField": "dentist_id", "as": "dn"}},
                {"$unwind": "$dn"},
                {"$project": {
                    "_id": 0, "plan_id": 1, "status": 1, "remaining": 1,
                    "sessions": 1, "estimated_end_date": 1,
                    "patient": {"$concat": ["$p.first_name", " ", "$p.last_name"]},
                    "phone": "$p.phone",
                    "dentist": {"$concat": ["دکتر ", "$dn.first_name", " ", "$dn.last_name"]},
                    "days_overdue": {"$dateDiff": {
                        "startDate": "$estimated_end_date", "endDate": now,
                        "unit": "day"}},
                }},
            ],
        }},
    ]).to_list(1)

    facets = result[0] if result else {}
    by_status = facets.get("by_status", [])
    overdue_total = (facets.get("overdue_total") or [{}])[0]
    open_totals = (facets.get("open") or [{}])[0]

    counts = {r["status"]: r["n"] for r in by_status}
    total = sum(counts.values())
    open_planned = open_totals.get("planned", 0)
    open_delivered = open_totals.get("delivered", 0)

    def rate(n: int) -> float:
        return round(n / total * 100, 1) if total else 0.0

    return {
        "by_status": by_status,
        "total_plans": total,
        # Every plan in this dataset was quoted; the ones the patient walked
        # away from are the cancelled ones, so acceptance is their complement.
        "acceptance_rate": rate(total - counts.get(PLAN_CANCELLED, 0)),
        "completion_rate": rate(counts.get(PLAN_DONE, 0)),
        "planned_value": sum(r["planned"] for r in by_status),
        "delivered_value": sum(r["delivered"] for r in by_status),
        "unrealised_value": max(open_planned - open_delivered, 0),
        "avg_plan_value": round(sum(r["planned"] for r in by_status) / total) if total else 0,
        "avg_sessions_per_plan": (
            round(sum(r["sessions"] for r in by_status) / total, 1) if total else 0
        ),
        "overdue_count": overdue_total.get("n", 0),
        "overdue_value": overdue_total.get("remaining", 0),
        "overdue_plans": facets.get("overdue_worst", []),
    }


async def patient_recall(db, f: Filters) -> dict:
    """Who has lapsed out of recall, and how much of each month is new blood.

    A dental practice is a retention business: a patient seen every six months
    for a decade is worth many times a one-off. Total patient count hides that
    entirely — it only ever goes up.
    """
    now = datetime.now(UTC)

    # Recall status is an as-of-today fact: has this patient been seen within
    # the last RECALL_DAYS. Deriving "last visit" from only the sessions
    # inside the filter window made every patient lapsed as soon as the user
    # looked at an older period — a 2025 window reported 0% recall and 52
    # lapsed patients, which is an artefact of the filter, not the clinic. The
    # window still drives the new/returning trend below, where a period
    # genuinely is the question being asked.
    undated = replace(f, date_from=None, date_to=None)

    last_visit, month_pairs, never = await asyncio.gather(
        db.treatment_sessions.aggregate([
            *session_pipeline(undated, need_patient=True),
            {"$group": {"_id": "$plan.patient_id",
                        "last": {"$max": "$session_date"},
                        "visits": {"$sum": 1},
                        "revenue": {"$sum": "$actual_cost"},
                        "name": {"$first": {"$concat": [
                            "$patient.first_name", " ", "$patient.last_name"]}},
                        "phone": {"$first": "$patient.phone"}}},
            {"$project": {"_id": 0, "patient_id": "$_id", "last": 1, "visits": 1,
                          "revenue": 1, "name": 1, "phone": 1}},
        ]).to_list(None),
        # Distinct (patient, month) pairs: enough to derive both the new and
        # the returning count for every month without a second pass.
        db.treatment_sessions.aggregate([
            *session_pipeline(f, need_patient=True),
            {"$group": {"_id": {
                "patient": "$plan.patient_id",
                "month": {"$dateToString": {"format": "%Y-%m", "date": "$session_date"}},
            }}},
            {"$project": {"_id": 0, "patient": "$_id.patient", "month": "$_id.month"}},
        ]).to_list(None),
        # Registered but never treated, counted from the patient side. The old
        # `all_patients - treated_in_window` turned every filter into a bigger
        # number: narrowing to one insurer reported all 463 other patients as
        # "registered, never treated" when they had simply been excluded.
        db.patients.aggregate([
            *patient_pipeline(f),
            {"$lookup": {"from": "treatment_plans", "localField": "patient_id",
                         "foreignField": "patient_id", "as": "plans"}},
            {"$lookup": {"from": "treatment_sessions", "localField": "plans.plan_id",
                         "foreignField": "plan_id", "as": "sess"}},
            {"$match": {"sess": {"$size": 0}}},
            {"$count": "n"},
        ]).to_list(1),
    )

    lapsed, active = [], 0
    for p in last_visit:
        last = p["last"]
        days = (now - (last if last.tzinfo else last.replace(tzinfo=UTC))).days
        p["days_since"] = days
        if days > RECALL_DAYS:
            lapsed.append(p)
        else:
            active += 1

    # Highest lifetime value first — reception has finite call time, and the
    # patient worth calling back is not the same as the longest absent one.
    lapsed.sort(key=lambda p: p["revenue"], reverse=True)

    first_month: dict[int, str] = {}
    for row in month_pairs:
        pid, month = row["patient"], row["month"]
        if pid not in first_month or month < first_month[pid]:
            first_month[pid] = month

    per_month: dict[str, dict] = {}
    for row in month_pairs:
        bucket = per_month.setdefault(row["month"], {"new": 0, "returning": 0})
        bucket["new" if first_month[row["patient"]] == row["month"] else "returning"] += 1

    new_vs_returning = [
        {"month": m, **v, "total": v["new"] + v["returning"]}
        for m, v in sorted(per_month.items())
    ]
    treated = len(last_visit)
    return {
        "active": active,
        "lapsed": len(lapsed),
        # Registered but never treated — a registration that never converted.
        "never_treated": never[0]["n"] if never else 0,
        "recall_rate": round(active / treated * 100, 1) if treated else 0,
        "recall_list": lapsed[:10],
        "recall_value_at_risk": sum(p["revenue"] for p in lapsed),
        "new_vs_returning": new_vs_returning,
        "recall_days": RECALL_DAYS,
    }


async def monthly_kpis(db, f: Filters) -> list[dict]:
    """One row per month carrying every headline KPI.

    Returned as a single series rather than six scalar endpoints because a
    KPI card needs three things from the same data — the value, the change
    against last month, and the shape of the trend behind it. Deriving all
    three client-side from one payload keeps them arithmetically consistent;
    computing the number in one place and the sparkline in another is how
    a card ends up disagreeing with its own graph.
    """
    month = {"$dateToString": {"format": "%Y-%m", "date": "$session_date"}}
    no_category = replace(f, category=None)

    sessions, payments, appointments, first_seen = await asyncio.gather(
        db.treatment_sessions.aggregate([
            *session_pipeline(f, need_patient=True),
            {"$group": {"_id": month,
                        "revenue": {"$sum": "$actual_cost"},
                        "sessions": {"$sum": 1},
                        "patients": {"$addToSet": "$plan.patient_id"}}},
            {"$project": {"_id": 1, "revenue": 1, "sessions": 1,
                          "patients": {"$size": "$patients"}}},
        ]).to_list(None),
        # Payments and appointments cannot be narrowed by service category
        # (filters.py), so the category filter is dropped for them rather than
        # applied to the session half only — a row mixing category-filtered
        # revenue with unfiltered collections is worse than one that is
        # consistently scoped and says so.
        db.payments.aggregate([
            *payment_pipeline(no_category),
            {"$group": {"_id": {"$dateToString": {"format": "%Y-%m", "date": "$payment_date"}},
                        "collected": {"$sum": "$amount"}}},
        ]).to_list(None),
        db.appointments.aggregate([
            *appointment_pipeline(no_category),
            {"$group": {
                "_id": {"$dateToString": {"format": "%Y-%m", "date": "$scheduled_datetime"}},
                "appointments": {"$sum": 1},
                "lost": {"$sum": {"$cond": [
                    {"$in": ["$status", [STATUS_CANCELLED, STATUS_NOSHOW]]}, 1, 0]}},
            }},
        ]).to_list(None),
        # A patient is "new" in the month of their first session ever, so this
        # deliberately ignores the date filter — otherwise narrowing the window
        # would relabel long-standing patients as new.
        db.treatment_sessions.aggregate([
            {"$lookup": {"from": "treatment_plans", "localField": "plan_id",
                         "foreignField": "plan_id", "as": "plan"}},
            {"$unwind": "$plan"},
            {"$group": {"_id": "$plan.patient_id", "first": {"$min": "$session_date"}}},
            {"$group": {"_id": {"$dateToString": {"format": "%Y-%m", "date": "$first"}},
                        "new_patients": {"$sum": 1}}},
        ]).to_list(None),
    )

    rows: dict[str, dict] = {}
    for source in (sessions, payments, appointments, first_seen):
        for r in source:
            if r["_id"]:
                rows.setdefault(r["_id"], {}).update(
                    {k: v for k, v in r.items() if k != "_id"})

    blank = {"revenue": 0, "collected": 0, "sessions": 0, "patients": 0,
             "new_patients": 0, "appointments": 0, "lost": 0}
    return [{"month": m, **blank, **rows[m]} for m in sorted(rows)]


async def lost_slot_cost(db, f: Filters) -> dict:
    """Cancellations and no-shows priced in tomans and chair-hours.

    Reporting a 12% no-show rate changes no behaviour. Reporting what those
    slots would have billed is the same number in the unit a clinic manager
    makes decisions in.
    """
    # A cancelled appointment never produced a session, so it has no service
    # and no category. The category filter is therefore dropped on both halves
    # — including the average session value, so the slot count and the price
    # put on it are always drawn from the same population.
    no_category = replace(f, category=None)
    statuses, value = await asyncio.gather(
        db.appointments.aggregate([
            *appointment_pipeline(no_category),
            {"$group": {"_id": None, "total": {"$sum": 1},
                        "cancelled": {"$sum": {"$cond": [{"$eq": ["$status", STATUS_CANCELLED]}, 1, 0]}},
                        "noshow": {"$sum": {"$cond": [{"$eq": ["$status", STATUS_NOSHOW]}, 1, 0]}}}},
        ]).to_list(1),
        db.treatment_sessions.aggregate([
            *session_pipeline(no_category),
            {"$group": {"_id": None, "avg": {"$avg": "$actual_cost"}}},
        ]).to_list(1),
    )

    s = statuses[0] if statuses else {"total": 0, "cancelled": 0, "noshow": 0}
    avg_value = round((value[0]["avg"] if value else 0) or 0)
    lost = s["cancelled"] + s["noshow"]

    return {
        "total": s["total"],
        "cancelled": s["cancelled"],
        "noshow": s["noshow"],
        "lost_slots": lost,
        "lost_rate": round(lost / s["total"] * 100, 1) if s["total"] else 0,
        "avg_session_value": avg_value,
        # Valued at the average completed session, which is the honest
        # estimate: a released slot is sometimes refilled, so this is a
        # ceiling on the loss, not a bill.
        "lost_revenue": lost * avg_value,
        "lost_chair_hours": round(lost * SLOT_MINUTES / 60, 1),
    }


# ------------------------------------------------ accounting (owner view)
#
# Everything above answers "what did we produce?". A clinic owner and an
# accountant also need "when does the money actually arrive?" and "what is
# left after we pay for it?" — neither of which any production chart can
# show, because both depend on costs and on time-to-cash rather than on
# treatment.


# Standard A/R ageing ladder. The last bucket is deliberately open-ended:
# past ninety days the exact age stops mattering and collectability is the
# only question left.
AGING_BUCKETS = (
    (0, 30, "۰ تا ۳۰ روز"),
    (31, 60, "۳۱ تا ۶۰ روز"),
    (61, 90, "۶۱ تا ۹۰ روز"),
    (91, None, "بیش از ۹۰ روز"),
)

# Mean days per month, used to turn a monthly payroll figure into the cost of
# an arbitrary reporting window.
DAYS_PER_MONTH = 30.44


def _bucket_for(age_days: int) -> str:
    for low, high, label in AGING_BUCKETS:
        if age_days >= low and (high is None or age_days <= high):
            return label
    return AGING_BUCKETS[0][2]


async def _window_days(db, f: Filters) -> int:
    """Length of the reporting window in days.

    Taken from the filter when it is bounded, otherwise from the span of the
    data itself, so an unfiltered page still divides by a real period instead
    of assuming one.
    """
    if f.date_from and f.date_to:
        return (f.date_to - f.date_from).days
    span = await db.treatment_sessions.aggregate([
        *session_pipeline(f),
        {"$group": {"_id": None, "min": {"$min": "$session_date"},
                    "max": {"$max": "$session_date"}}},
    ]).to_list(1)
    if span and span[0].get("min") and span[0].get("max"):
        return (span[0]["max"] - span[0]["min"]).days
    return 0


async def receivables_aging(db, f: Filters) -> dict:
    """A/R ageing ladder, DSO, and how long invoices actually take to settle.

    `receivables()` already reports how much is outstanding. It cannot say
    whether that money is two weeks old or two years old — and those are
    completely different problems. A single outstanding total looks the same
    whether every invoice is current or half of them are uncollectable.

    Ages run from today, not from the end of the filter window: an invoice
    raised in Farvardin is 120 days old now regardless of which months the
    viewer happens to be looking at.
    """
    now = datetime.now(UTC)

    rows = await db.invoices.aggregate([
        *invoice_pipeline(f),
        {"$lookup": {"from": "payments", "localField": "invoice_id",
                     "foreignField": "invoice_id", "as": "pay"}},
        {"$lookup": {"from": "patients", "localField": "patient_id",
                     "foreignField": "patient_id", "as": "pt"}},
        {"$addFields": {
            "paid": {"$sum": "$pay.amount"},
            "settled_on": {"$max": "$pay.payment_date"},
        }},
        {"$project": {
            "_id": 0, "invoice_id": 1, "issue_date": 1, "status": 1,
            "patient_share": 1, "paid": 1, "settled_on": 1,
            "balance": {"$subtract": ["$patient_share", "$paid"]},
            "age_days": {"$dateDiff": {
                "startDate": "$issue_date", "endDate": now, "unit": "day"}},
            "days_to_settle": {"$cond": [
                {"$gt": [{"$size": "$pay"}, 0]},
                {"$dateDiff": {"startDate": "$issue_date",
                               "endDate": {"$max": "$pay.payment_date"},
                               "unit": "day"}},
                None,
            ]},
            "patient": {"$concat": [
                {"$first": "$pt.first_name"}, " ", {"$first": "$pt.last_name"}]},
            "phone": {"$first": "$pt.phone"},
        }},
    ]).to_list(None)

    billed = sum(r["patient_share"] for r in rows)
    collected = sum(r["paid"] for r in rows)
    # Only positive balances are receivable. An overpaid invoice is a credit
    # to refund, not negative debt to net off against someone else's arrears.
    open_rows = [r for r in rows if r["balance"] > 0]
    outstanding = sum(r["balance"] for r in open_rows)

    totals = {label: {"bucket": label, "n": 0, "amount": 0}
              for _, _, label in AGING_BUCKETS}
    for r in open_rows:
        bucket = totals[_bucket_for(r["age_days"] or 0)]
        bucket["n"] += 1
        bucket["amount"] += r["balance"]

    settled = [r["days_to_settle"] for r in rows if r["days_to_settle"] is not None]
    # Category is dropped here too. Every figure above comes from invoices,
    # which carry no service category, so taking the window length from a
    # category-filtered session span would divide a clinic-wide receivable by
    # one category's worth of days and report a DSO that belongs to neither.
    days = await _window_days(db, replace(f, category=None))

    return {
        "billed": billed,
        "collected": collected,
        "outstanding": outstanding,
        "buckets": list(totals.values()),
        # Days Sales Outstanding: at the current billing rate, how many days
        # of revenue are sitting unpaid. Comparable across clinic sizes in a
        # way that a toman figure is not.
        "dso": round(outstanding / billed * days) if billed and days else 0,
        "avg_days_to_settle": round(sum(settled) / len(settled), 1) if settled else 0,
        # Share of receivables older than ninety days — the single number that
        # says whether collections are working.
        "over_90_share": round(
            totals[AGING_BUCKETS[-1][2]]["amount"] / outstanding * 100, 1
        ) if outstanding else 0,
        "window_days": days,
        # Biggest debts first: collection time is finite, and chasing the
        # oldest invoice is not the same as chasing the most valuable one.
        "worst": sorted(open_rows, key=lambda r: r["balance"], reverse=True)[:10],
    }


async def profitability(db, f: Filters) -> dict:
    """What each service leaves behind after the costs of delivering it.

    Revenue per service was already on the revenue page, but revenue is not
    profit: the two largest costs in a dental clinic — the material consumed
    and the dentist's commission — vary enormously between services. A
    high-revenue implant with 45% commission and expensive components can
    contribute less than a cheap, fast, material-free check-up.

    Three costs are subtracted, and it is worth being explicit about which:
      * material — actual consumable usage recorded against the session
      * commission — the dentist's own percentage of what they billed
      * payroll — salaried staff, apportioned across the window, which is a
        clinic-wide overhead and therefore reported at the total level only,
        never per service (splitting it per service would be an invention)
    """
    per_service, staff, days = await asyncio.gather(
        db.treatment_sessions.aggregate([
            *session_pipeline(f, need_service=True, need_dentist=True),
            {"$lookup": {"from": "consumable_usage", "localField": "session_id",
                         "foreignField": "session_id", "as": "usage"}},
            {"$unwind": {"path": "$usage", "preserveNullAndEmptyArrays": True}},
            {"$lookup": {"from": "consumables", "localField": "usage.consumable_id",
                         "foreignField": "consumable_id", "as": "c"}},
            {"$unwind": {"path": "$c", "preserveNullAndEmptyArrays": True}},
            # One row per session before anything is summed, so a session that
            # consumed three materials does not contribute its revenue thrice.
            {"$group": {
                "_id": "$session_id",
                "service_id": {"$first": "$service.service_id"},
                "name": {"$first": "$service.name"},
                "category": {"$first": "$service.category"},
                "revenue": {"$first": "$actual_cost"},
                "list_price": {"$first": "$service.base_price"},
                "rate": {"$first": "$dentist.commission_rate"},
                "material": {"$sum": {"$multiply": [
                    {"$ifNull": ["$usage.quantity_used", 0]},
                    {"$ifNull": ["$c.unit_price", 0]}]}},
            }},
            {"$group": {
                "_id": "$service_id",
                "name": {"$first": "$name"},
                "category": {"$first": "$category"},
                "sessions": {"$sum": 1},
                "revenue": {"$sum": "$revenue"},
                "list_value": {"$sum": "$list_price"},
                "material_cost": {"$sum": "$material"},
                "commission": {"$sum": {"$multiply": [
                    "$revenue", {"$divide": [{"$ifNull": ["$rate", 0]}, 100]}]}},
            }},
        ]).to_list(None),
        db.staff.aggregate([
            {"$group": {"_id": None, "monthly": {"$sum": "$salary"}, "n": {"$sum": 1}}},
        ]).to_list(1),
        _window_days(db, f),
    )

    services = []
    for r in per_service:
        revenue = r["revenue"]
        margin = revenue - r["material_cost"] - r["commission"]
        services.append({
            "service_id": r["_id"],
            "name": r["name"],
            "category": r["category"],
            "sessions": r["sessions"],
            "revenue": revenue,
            "material_cost": round(r["material_cost"]),
            "commission": round(r["commission"]),
            "gross_margin": round(margin),
            "margin_pct": round(margin / revenue * 100, 1) if revenue else 0,
            # Negative means the service was billed below its own list price.
            "discount": round(r["list_value"] - revenue),
        })
    # Weakest margin percentage first: this table exists to find the services
    # that are busy rather than profitable, and those sort to the bottom on
    # every other page in the panel.
    services.sort(key=lambda s: s["margin_pct"])

    revenue = sum(s["revenue"] for s in services)
    material = sum(s["material_cost"] for s in services)
    commission = sum(s["commission"] for s in services)
    list_value = sum(r["list_value"] for r in per_service)

    monthly_payroll = staff[0]["monthly"] if staff else 0
    months = days / DAYS_PER_MONTH if days else 0
    payroll = round(monthly_payroll * months)

    return {
        "services": services,
        "totals": {
            "revenue": revenue,
            "material_cost": material,
            "commission": round(commission),
            "payroll": payroll,
            "gross_margin": round(revenue - material - commission),
            # After salaried staff as well — the closest this data gets to a
            # bottom line. Rent, utilities and equipment are not recorded
            # anywhere, so this is still above net profit, not equal to it.
            "operating_margin": round(revenue - material - commission - payroll),
            "material_pct": round(material / revenue * 100, 1) if revenue else 0,
            "commission_pct": round(commission / revenue * 100, 1) if revenue else 0,
            "payroll_pct": round(payroll / revenue * 100, 1) if revenue else 0,
            "margin_pct": round(
                (revenue - material - commission) / revenue * 100, 1) if revenue else 0,
        },
        # Billed against list price. Every toman here is pure margin that was
        # given away at the desk, and it appears on no other report.
        "discount": {
            "list_value": round(list_value),
            "billed": revenue,
            "given_away": round(list_value - revenue),
            "pct": round((list_value - revenue) / list_value * 100, 2) if list_value else 0,
        },
        "payroll": {
            "headcount": staff[0]["n"] if staff else 0,
            "monthly": monthly_payroll,
            "window_cost": payroll,
            "months": round(months, 1),
        },
        "window_days": days,
    }
