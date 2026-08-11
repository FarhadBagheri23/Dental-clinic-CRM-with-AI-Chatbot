"""Global dashboard filters (report §۷ — فیلترهای سراسری).

Date range, dentist specialty, service category and insurance company apply
across every page, so the match stages are built once here rather than
re-derived in each pipeline.

Not every filter can reach every collection, and the ones that cannot are
declared rather than approximated:

* **category on `appointments`** — a cancelled or no-show appointment has no
  treatment_session, so it has no service. Joining through the session to
  filter by category would silently delete exactly the rows a cancellation
  chart exists to show, turning a 12% no-show rate into 0%.
* **category on `invoices` / `payments`** — an invoice covers a whole
  treatment plan, which normally spans several categories. There is no single
  category to match, and pro-rating one would report an estimate as a fact.

`UNSUPPORTED_FILTERS` below names those combinations. It is served to the
client with the filter options, so a chart can state the filter it could not
honour instead of showing an unfiltered number under a filtered header.
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

    def date_match(self, field: str) -> dict:
        """A $match fragment for the given date field, or {} if unbounded."""
        bounds = {}
        if self.date_from:
            bounds["$gte"] = self.date_from
        if self.date_to:
            bounds["$lte"] = self.date_to
        return {field: bounds} if bounds else {}

    def date_stage(self, field: str) -> list[dict]:
        """`[{"$match": ...}]` for the given date field, or `[]` if unbounded.

        Spread into a pipeline (`*f.date_stage("session_date")`) so an
        unfiltered pipeline carries no empty stage.
        """
        match = self.date_match(field)
        return [{"$match": match}] if match else []


# Filters a given analytics endpoint cannot honour, keyed by its path segment.
# Served to the client by /analytics/filters. `test_filters.py` asserts each
# entry is true — that setting the filter really does leave the response
# unchanged — so this cannot quietly drift from the pipelines above.
UNSUPPORTED_FILTERS = {
    "appointment-trend": ["category"],
    "heatmap": ["category"],
    "lost-slots": ["category"],
    "receivables": ["category"],
    "payment-methods": ["category"],
    "treatment-plans": ["category"],
    # Invoice-rooted, so it inherits the same limitation as `receivables`.
    "aging": ["category"],
}


# ------------------------------------------------------ join fragments

def _patient_insurance(local: str) -> list[dict]:
    """patients + insurance join, from a collection holding a patient id."""
    return [
        {"$lookup": {"from": "patients", "localField": local,
                     "foreignField": "patient_id", "as": "patient"}},
        {"$unwind": "$patient"},
        {"$lookup": {"from": "insurance", "localField": "patient.insurance_id",
                     "foreignField": "insurance_id", "as": "insurer"}},
    ]


def _plan_dentist(local: str = "plan_id") -> list[dict]:
    """treatment_plans + dentists join, from a collection holding a plan id."""
    return [
        {"$lookup": {"from": "treatment_plans", "localField": local,
                     "foreignField": "plan_id", "as": "plan"}},
        {"$unwind": "$plan"},
        {"$lookup": {"from": "dentists", "localField": "plan.dentist_id",
                     "foreignField": "dentist_id", "as": "dentist"}},
        {"$unwind": "$dentist"},
    ]


def _dentist_direct() -> list[dict]:
    """dentists join, from a collection holding dentist_id itself."""
    return [
        {"$lookup": {"from": "dentists", "localField": "dentist_id",
                     "foreignField": "dentist_id", "as": "dentist"}},
        {"$unwind": "$dentist"},
    ]


# --------------------------------------------------------- pipelines

def session_pipeline(f: Filters, *, need_service=False, need_dentist=False,
                     need_patient=False) -> list[dict]:
    """Lookup + match stages for a treatment_sessions pipeline.

    Joins are added only when a filter or the caller actually needs them —
    an unconditional four-way $lookup over 2,400 sessions is wasted work on
    a page that only groups by service.
    """
    stages = f.date_stage("session_date")

    want_dentist = need_dentist or f.specialty is not None
    want_service = need_service or f.category is not None
    want_patient = need_patient or f.insurance is not None

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


def appointment_pipeline(f: Filters) -> list[dict]:
    """Filter stages for an `appointments` pipeline.

    `category` is not honoured — see the module docstring. Callers report it
    with `ignored(f, "category")`.
    """
    stages = f.date_stage("scheduled_datetime")
    if f.specialty:
        stages += _dentist_direct()
        stages.append({"$match": {"dentist.specialty": f.specialty}})
    if f.insurance:
        stages += _patient_insurance("patient_id")
        stages.append({"$match": {"insurer.company_name": f.insurance}})
    return stages


def invoice_pipeline(f: Filters) -> list[dict]:
    """Filter stages for an `invoices` pipeline. `category` is not honoured."""
    stages = f.date_stage("issue_date")
    if f.insurance:
        stages += _patient_insurance("patient_id")
        stages.append({"$match": {"insurer.company_name": f.insurance}})
    if f.specialty:
        stages += _plan_dentist()
        stages.append({"$match": {"dentist.specialty": f.specialty}})
    return stages


def payment_pipeline(f: Filters) -> list[dict]:
    """Filter stages for a `payments` pipeline. `category` is not honoured.

    Specialty and insurer both hang off the invoice the payment settles, so
    the invoice join is added once and shared.
    """
    stages = f.date_stage("payment_date")
    if f.insurance or f.specialty:
        stages += [
            {"$lookup": {"from": "invoices", "localField": "invoice_id",
                         "foreignField": "invoice_id", "as": "inv"}},
            {"$unwind": "$inv"},
        ]
    if f.insurance:
        stages += _patient_insurance("inv.patient_id")
        stages.append({"$match": {"insurer.company_name": f.insurance}})
    if f.specialty:
        stages += _plan_dentist("inv.plan_id")
        stages.append({"$match": {"dentist.specialty": f.specialty}})
    return stages


def plan_pipeline(f: Filters) -> list[dict]:
    """Filter + delivered-value stages for a `treatment_plans` pipeline.

    `category` is not honoured: a plan spans several services. Delivered value
    comes from the sessions actually performed against the plan, not from the
    invoice — an invoice is raised once, while a plan is worked through over
    months.
    """
    stages = f.date_stage("start_date")
    if f.specialty:
        stages += _dentist_direct()
        stages.append({"$match": {"dentist.specialty": f.specialty}})
    if f.insurance:
        stages += _patient_insurance("patient_id")
        stages.append({"$match": {"insurer.company_name": f.insurance}})
    stages += [
        {"$lookup": {"from": "treatment_sessions", "localField": "plan_id",
                     "foreignField": "plan_id", "as": "s"}},
        {"$addFields": {"delivered": {"$sum": "$s.actual_cost"},
                        "sessions": {"$size": "$s"}}},
    ]
    return stages


def patient_pipeline(f: Filters) -> list[dict]:
    """Filter stages for a `patients` pipeline.

    Only the insurer is a patient attribute. Specialty and category describe
    treatment, so a patient who has never been treated has neither — applying
    them here would filter out the very rows a "registered, never treated"
    figure is counting.
    """
    if not f.insurance:
        return []
    return [
        {"$lookup": {"from": "insurance", "localField": "insurance_id",
                     "foreignField": "insurance_id", "as": "ins"}},
        {"$match": {"ins.company_name": f.insurance}},
    ]
