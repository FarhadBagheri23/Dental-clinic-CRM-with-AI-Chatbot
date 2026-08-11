"""Turning what a clinic owner says about time into a date range.

Owners ask «مرداد چقدر درآمد داشتیم؟», not «from 2026-07-23 to 2026-08-22».
Language models are unreliable at Jalali↔Gregorian arithmetic — the leap rule
is a 33-year cycle — so the conversion is done here with `jdatetime` and the
model only has to name the period.
"""

from datetime import datetime, time

import jdatetime

JALALI_MONTHS = [
    "فروردین", "اردیبهشت", "خرداد", "تیر", "مرداد", "شهریور",
    "مهر", "آبان", "آذر", "دی", "بهمن", "اسفند",
]
# Spelling variants that appear in real typing.
_ALIASES = {"اسپند": "اسفند", "امرداد": "مرداد", "شهريور": "شهریور"}

# First six Jalali months are 31 days, next five are 30, Esfand is 29 or 30.
def _month_length(year: int, month: int) -> int:
    if month <= 6:
        return 31
    if month <= 11:
        return 30
    return 30 if jdatetime.date(year, 1, 1).isleap() else 29


def today_jalali() -> jdatetime.date:
    return jdatetime.date.fromgregorian(date=datetime.now().date())


def jalali_month_range(year: int, month: int) -> tuple[datetime, datetime]:
    """Gregorian [start, end] datetimes covering one whole Jalali month."""
    if not 1 <= month <= 12:
        raise ValueError(f"Jalali month must be 1–12, got {month}")
    start = jdatetime.date(year, month, 1).togregorian()
    end = jdatetime.date(year, month, _month_length(year, month)).togregorian()
    # Inclusive of the last day: the filters compare against a datetime, so an
    # end of midnight would silently drop everything after 00:00 on that day.
    return datetime.combine(start, time.min), datetime.combine(end, time.max)


def jalali_year_range(year: int) -> tuple[datetime, datetime]:
    start = jdatetime.date(year, 1, 1).togregorian()
    end = jdatetime.date(year, 12, _month_length(year, 12)).togregorian()
    return datetime.combine(start, time.min), datetime.combine(end, time.max)


def month_number(name: str) -> int | None:
    """Jalali month name -> 1-12, tolerant of spelling variants."""
    from app.agent.normalize import normalize

    wanted = normalize(_ALIASES.get(name.strip(), name))
    for i, month in enumerate(JALALI_MONTHS, start=1):
        if normalize(month) == wanted:
            return i
    return None


def resolve(period: str | None = None, year: int | None = None) -> tuple[datetime, datetime] | None:
    """Resolve a named period to a Gregorian range, or None for all-time.

    Accepts a Jalali month name («مرداد»), `this_month`, `last_month`,
    `this_year`, or None. `year` defaults to the current Jalali year.
    """
    if not period:
        return None

    now = today_jalali()
    year = year or now.year

    if period == "this_year":
        return jalali_year_range(year)
    if period == "this_month":
        return jalali_month_range(now.year, now.month)
    if period == "last_month":
        # Month 1 rolls back to Esfand of the previous year.
        return (jalali_month_range(now.year - 1, 12) if now.month == 1
                else jalali_month_range(now.year, now.month - 1))

    month = month_number(period)
    if month is None:
        raise ValueError(
            f"ناشناخته: {period!r}. یکی از نام‌های ماه شمسی یا "
            "this_month / last_month / this_year را بدهید."
        )
    return jalali_month_range(year, month)
