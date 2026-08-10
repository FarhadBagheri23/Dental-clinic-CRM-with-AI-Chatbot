"""Global dashboard filters (report §۷ — فیلترهای سراسری).

Date range, dentist specialty, service category and insurance company apply
across every page, so the match stages are built once here rather than
re-derived in each pipeline.
"""

from dataclasses import dataclass
from datetime import datetime

# Joins needed to reach each filterable field from treatment_sessions.
LOOKUP_PLAN = [
    {"$lookup": {"from": "treatment_plans", "localField": "plan_id",
                 "foreignField": "plan_id", "as": "plan"}},
    {"$unwind": "$plan"},
]
LOOKUP_DENTIST = [
    {"$lookup": {"from": "dentists", "localField": "plan.dentist_id",
                 "foreignField": "dentist_id", "as": "dentist"}},
    {"$unwind": "$dentist"},
]
LOOKUP_SERVICE = [
    {"$lookup": {"from": "services", "localField": "service_id",
                 "foreignField": "service_id", "as": "service"}},
    {"$unwind": "$service"},
]
LOOKUP_PATIENT = [
    {"$lookup": {"from": "patients", "localField": "plan.patient_id",
                 "foreignField": "patient_id", "as": "patient"}},
    {"$unwind": "$patient"},
    {"$lookup": {"from": "insurance", "localField": "patient.insurance_id",
                 "foreignField": "insurance_id", "as": "insurer"}},
]


@dataclass(frozen=True)
class Filters:
    date_from: datetime | None = None
    date_to: datetime | None = None
    specialty: str | None = None
    category: str | None = None
    insurance: str | None = None

    @property
    def needs_dentist(self) -> bool:
        return self.specialty is not None

    @property
    def needs_service(self) -> bool:
        return self.category is not None

    @property
    def needs_patient(self) -> bool:
        return self.insurance is not None

    def date_match(self, field: str) -> dict:
        """A $match fragment for the given date field, or {} if unbounded."""
        bounds = {}
        if self.date_from:
            bounds["$gte"] = self.date_from
        if self.date_to:
            bounds["$lte"] = self.date_to
        return {field: bounds} if bounds else {}


def session_pipeline(f: Filters, *, need_service=False, need_dentist=False,
                     need_patient=False) -> list[dict]:
    """Lookup + match stages for a treatment_sessions pipeline.

    Joins are added only when a filter or the caller actually needs them —
    an unconditional four-way $lookup over 2,400 sessions is wasted work on
    a page that only groups by service.
    """
    stages: list[dict] = []
    date = f.date_match("session_date")
    if date:
        stages.append({"$match": date})

    want_dentist = need_dentist or f.needs_dentist
    want_service = need_service or f.needs_service
    want_patient = need_patient or f.needs_patient

    if want_dentist or want_patient:
        stages += LOOKUP_PLAN
    if want_dentist:
        stages += LOOKUP_DENTIST
    if want_service:
        stages += LOOKUP_SERVICE
    if want_patient:
        stages += LOOKUP_PATIENT

    match = {}
    if f.specialty:
        match["dentist.specialty"] = f.specialty
    if f.category:
        match["service.category"] = f.category
    if f.insurance:
        match["insurer.company_name"] = f.insurance
    if match:
        stages.append({"$match": match})

    return stages


def appointment_match(f: Filters) -> dict:
    """Appointments carry no service or insurance link, so only date and
    specialty (via dentist) narrow them."""
    return f.date_match("scheduled_datetime")
