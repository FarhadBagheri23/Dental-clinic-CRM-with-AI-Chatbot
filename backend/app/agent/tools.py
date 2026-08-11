"""The assistant's tools.

The design rule here is the one that decides whether an owner trusts this
thing: **the assistant does not compute. It calls the same aggregations the
dashboard calls.**

Letting a model write its own queries produces answers that disagree with the
panel on screen — different commission handling, a different recall window, a
different capacity denominator. The first time an owner catches that, they
stop believing both. So every number below comes from `app.repositories`,
already tested, already rendered on a page they can cross-check.

Retrieval (`search_documents`) is for prose only: what a service is, what an
insurer covers, how a front-desk procedure runs. Never for numbers.

Tools are plain async functions rather than LangChain objects so they can be
tested without a model, a key, or a network.
"""

from dataclasses import dataclass
from typing import Any

from app.agent.period import JALALI_MONTHS, resolve, today_jalali
from app.agent.retrieve import Index
from app.repositories import analytics as A
from app.repositories import dashboard as D
from app.repositories.filters import Filters


def _filters(period: str | None = None, year: int | None = None,
             specialty: str | None = None, category: str | None = None,
             insurance: str | None = None) -> Filters:
    span = resolve(period, year)
    return Filters(
        date_from=span[0] if span else None,
        date_to=span[1] if span else None,
        specialty=specialty, category=category, insurance=insurance,
    )


def _money(n) -> int:
    return round(n or 0)


@dataclass
class Toolbox:
    """Bound to one database and one retrieval index.

    `owner` gates the same fields the REST API redacts. It is enforced here,
    on the data, rather than only in the system prompt: a prompt asking the
    model not to mention a phone number still hands it the phone number.
    """
    db: Any
    index: Index
    owner: bool = True

    # -------------------------------------------------------- retrieval

    async def search_documents(self, query: str, limit: int = 4) -> dict:
        """خدمات، پوشش بیمه‌ها و رویه‌های کلینیک را جست‌وجو می‌کند.

        برای پرسش‌های توصیفی: «ایمپلنت چیست»، «بیمه دانا چه چیزی را پوشش
        می‌دهد»، «رویه رزرو نوبت چگونه است». برای عدد و مبلغ از این ابزار
        استفاده نکن.
        """
        hits = self.index.search(query, limit=limit)
        return {
            "results": [
                {"title": h.document.title, "text": h.document.text,
                 "source": h.document.source, "score": h.score}
                for h in hits
            ],
            "found": len(hits),
        }

    # ------------------------------------------------------------ money

    async def revenue_overview(self, period: str | None = None, year: int | None = None) -> dict:
        """درآمد، وصولی، مطالبات معوق و سهم بیمه در یک بازه.

        `period`: نام ماه شمسی («مرداد») یا this_month / last_month / this_year.
        بدون `period` کل بازه داده گزارش می‌شود.
        """
        f = _filters(period, year)
        rec = await A.receivables(self.db, f)
        cats = await A.revenue_by_category(self.db, f)
        return {
            "period": period or "کل بازه",
            "billed": _money(rec["billed"]),
            "collected": _money(rec["collected"]),
            "outstanding": _money(rec["outstanding"]),
            "insurance_covered": _money(rec["insurance"]),
            # Cash in the window vs cash against the window's own invoices.
            # Only the second may be turned into a rate; the first routinely
            # exceeds what was billed that month because it settles older
            # invoices, which produced a "441% collection rate" before this
            # was split apart.
            "collected_cash_in_period": _money(rec["collected"]),
            "collected_on_period_invoices": _money(rec["collected_on_window_invoices"]),
            "collection_rate_pct": rec["collection_rate"],
            "revenue_by_category": [
                {"category": c["category"], "revenue": _money(c["revenue"]),
                 "sessions": c["sessions"]} for c in cats
            ],
            "source": "receivables + revenue_by_category",
        }

    async def top_services(self, period: str | None = None, limit: int = 5,
                           year: int | None = None) -> dict:
        """پردرآمدترین خدمات، همراه با درآمد به ازای هر ساعت یونیت.

        رتبه‌بندی بر پایه درآمد ناخالص گمراه‌کننده است؛ `revenue_per_hour`
        نشان می‌دهد کدام خدمت واقعاً از زمان یونیت پول می‌سازد.
        """
        rows = await A.service_mix(self.db, _filters(period, year), limit)
        return {
            "period": period or "کل بازه",
            "services": [
                {"name": r["name"], "category": r["category"],
                 "revenue": _money(r["revenue"]), "sessions": r["sessions"],
                 "avg_ticket": _money(r["avg_ticket"]),
                 "revenue_per_chair_hour": _money(r["revenue_per_hour"])}
                for r in rows
            ],
            "source": "service_mix",
        }

    async def dentist_performance(self, period: str | None = None,
                                  specialty: str | None = None,
                                  year: int | None = None) -> dict:
        """عملکرد پزشکان: درآمد، کمیسیون، سهم خالص کلینیک و نرخ لغو/غیبت.

        نرخ کمیسیون بین ۲۵ تا ۴۵ درصد متفاوت است، پس پزشکِ با بیشترین درآمد
        همیشه بیشترین سود را برای کلینیک نمی‌سازد — به `clinic_margin` نگاه کن.
        """
        rows = await A.dentist_scorecard(self.db, _filters(period, year, specialty=specialty))
        return {
            "period": period or "کل بازه",
            "dentists": [
                {"name": r["name"], "specialty": r["specialty"],
                 "revenue": _money(r["revenue"]), "sessions": r["sessions"],
                 "patients": r["patients"],
                 "cancel_rate_pct": r["cancel_rate"],
                 "noshow_rate_pct": r["noshow_rate"],
                 **({"commission_rate_pct": r["commission_rate"],
                     "clinic_margin": _money(r["margin"])} if self.owner else {})}
                for r in rows
            ],
            "source": "dentist_scorecard",
        }

    # ----------------------------------------------------- operations

    async def appointment_losses(self, period: str | None = None,
                                 year: int | None = None) -> dict:
        """نوبت‌های لغوشده و غیبت‌ها، همراه با برآورد درآمد ازدست‌رفته به تومان."""
        r = await A.lost_slot_cost(self.db, _filters(period, year))
        return {"period": period or "کل بازه", **{
            "total_appointments": r["total"], "cancelled": r["cancelled"],
            "noshow": r["noshow"], "lost_slots": r["lost_slots"],
            "lost_rate_pct": r["lost_rate"],
            "lost_revenue": _money(r["lost_revenue"]),
            "lost_chair_hours": r["lost_chair_hours"],
        }, "source": "lost_slot_cost"}

    async def chair_utilisation(self, period: str | None = None,
                                year: int | None = None) -> dict:
        """بهره‌وری یونیت‌ها: زمان واقعی خدمات تقسیم بر ساعات نیروگذاری‌شده.

        هر یونیت شیفت متفاوتی دارد، پس بهره‌وری هر یونیت را جدا گزارش کن؛
        میانگین کلی تفاوت شیفت‌ها را پنهان می‌کند.
        """
        r = await A.chair_utilisation(self.db, _filters(period, year))
        return {
            "period": period or "کل بازه",
            "overall_utilisation_pct": r["overall_utilisation"],
            "booked_hours": r["booked_hours"],
            "capacity_hours": r["capacity_hours"],
            "chairs": [
                {"chair": c["chair"], "shift": c["shift"],
                 "staffed_hours_per_day": c["staffed_hours_per_day"],
                 "booked_hours": c["booked_hours"],
                 "utilisation_pct": c["utilisation"]}
                for c in r["chairs"]
            ],
            "source": "chair_utilisation",
        }

    # ------------------------------------------------------- clinical

    async def treatment_plan_status(self, period: str | None = None,
                                    year: int | None = None) -> dict:
        """وضعیت طرح‌های درمان: نرخ پذیرش، نرخ تکمیل، و ارزش درمانِ
        تأییدشده‌ای که هنوز انجام نشده — به همراه طرح‌های عقب‌افتاده."""
        r = await A.treatment_plans(self.db, _filters(period, year))
        return {
            "period": period or "کل بازه",
            "total_plans": r["total_plans"],
            "acceptance_rate_pct": r["acceptance_rate"],
            "completion_rate_pct": r["completion_rate"],
            "unrealised_value": _money(r["unrealised_value"]),
            "avg_plan_value": _money(r["avg_plan_value"]),
            "overdue_count": r["overdue_count"],
            "overdue_value": _money(r["overdue_value"]),
            "overdue_plans": [
                {"dentist": p["dentist"], "days_overdue": p["days_overdue"],
                 "remaining": _money(p["remaining"]),
                 **({"patient": p["patient"]} if self.owner else {})}
                for p in r["overdue_plans"][:5]
            ],
            "source": "treatment_plans",
        }

    async def patient_recall(self, period: str | None = None,
                             year: int | None = None) -> dict:
        """بیماران فعال، لغزیده از دوره فراخوان، و ثبت‌نام‌شده‌های بدون درمان.

        فهرست تماس بر پایه ارزش بیمار مرتب شده، نه طول غیبت.
        """
        r = await A.patient_recall(self.db, _filters(period, year))
        return {
            "active": r["active"], "lapsed": r["lapsed"],
            "never_treated": r["never_treated"],
            "recall_rate_pct": r["recall_rate"],
            "recall_window_days": r["recall_days"],
            "value_at_risk": _money(r["recall_value_at_risk"]),
            "call_list": [
                {"days_since_visit": p["days_since"], "visits": p["visits"],
                 "lifetime_value": _money(p["revenue"]),
                 **({"patient": p["name"]} if self.owner else {})}
                for p in r["recall_list"][:5]
            ],
            "source": "patient_recall",
        }

    async def low_stock(self) -> dict:
        """اقلام مصرفی که به حد سفارش رسیده‌اند یا از آن پایین‌ترند."""
        rows = await D.get_low_stock(self.db)
        return {
            "items": [
                {"name": c["name"], "stock": c["stock_quantity"], "unit": c["unit"],
                 "reorder_level": c["min_stock_level"], "supplier": c.get("supplier"),
                 "critical": c["critical"]}
                for c in rows
            ],
            "critical_count": sum(1 for c in rows if c["critical"]),
            "source": "get_low_stock",
        }

    async def clinic_context(self) -> dict:
        """تاریخ امروز و بازه‌ای که داده‌ها پوشش می‌دهند.

        قبل از پاسخ به هر پرسشِ وابسته به زمان («این ماه»، «پارسال») این را
        صدا بزن؛ حدس‌زدن تاریخ امروز خطای رایج است.
        """
        options = await A.get_filter_options(self.db)
        today = today_jalali()
        return {
            "today_jalali": f"{today.year}-{today.month:02d}-{today.day:02d}",
            "today_month_name": JALALI_MONTHS[today.month - 1],
            "data_from": options["date_min"].isoformat() if options["date_min"] else None,
            "data_to": options["date_max"].isoformat() if options["date_max"] else None,
            "specialties": options["specialties"],
            "service_categories": options["categories"],
            "insurers": options["insurers"],
        }


# Ordered so the model reads the context tool first. Names match the methods.
TOOL_NAMES = [
    "clinic_context", "search_documents", "revenue_overview", "top_services",
    "dentist_performance", "appointment_losses", "chair_utilisation",
    "treatment_plan_status", "patient_recall", "low_stock",
]
