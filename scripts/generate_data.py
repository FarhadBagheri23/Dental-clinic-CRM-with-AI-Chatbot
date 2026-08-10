#!/usr/bin/env python3
"""Synthetic data generator for the Dental Clinic BI project.

Emits 12 CSVs into data/ matching dental_clinic_erd.dbml exactly (column
names, order, types, nullability, FKs). Every business rule listed in the
project brief is enforced at generation time and re-checked afterwards by
validate(), which reads back only the in-memory rows it produced.

Usage:  python scripts/generate_data.py
"""

import csv
import json
import random
import re
from collections import Counter, defaultdict
from datetime import date, datetime, time, timedelta
from pathlib import Path

from faker import Faker

SEED = 42
random.seed(SEED)
Faker.seed(SEED)
fake = Faker("fa_IR")

TODAY = date.today()
DATA_DIR = Path(__file__).resolve().parent.parent / "data"
# The clinic website renders its roster and catalogue from this file.
SITE_DATA_PATH = Path(__file__).resolve().parent.parent / "website" / "app" / "clinic-data.json"

# Row counts. treatment_sessions is derived: exactly one per انجام‌شده
# appointment (TreatmentSession.appointment_id is UNIQUE NOT NULL), so
# 3000 appointments x 80% = 2400.
N_PATIENTS = 500
N_DENTISTS = 8
N_STAFF = 6
N_SERVICES = 25
N_APPOINTMENTS = 3000
N_PLANS = 400
N_SESSIONS = 2400
N_INVOICES = 400
N_PAYMENTS = 600
N_CONSUMABLES = 30
N_USAGE = 4000

STATUS_MIX = {"انجام‌شده": 2400, "لغو": 240, "غایب": 150, "رزرو": 210}

CHAIRS = [1, 2, 3, 4, 5, 6]
# 08:00..20:30 start times, 30-minute grid.
SLOTS = [time(h, m) for h in range(8, 21) for m in (0, 30)][:-1]

MALE_FIRST = [
    "علی", "محمد", "رضا", "حسین", "امیر", "مهدی", "سعید", "احمد", "مجید", "بهرام",
    "فرهاد", "کامران", "نیما", "آرش", "پویا", "سینا", "بابک", "داریوش", "شهرام", "وحید",
    "یاسر", "کاوه", "سامان", "میلاد", "پدرام", "ایمان", "حامد", "نوید", "فرزاد", "اردشیر",
]
FEMALE_FIRST = [
    "زهرا", "فاطمه", "مریم", "سارا", "نرگس", "الهام", "شیرین", "پریسا", "نگار", "لیلا",
    "مینا", "سمیرا", "آزاده", "بهاره", "رویا", "شادی", "مهسا", "نسرین", "یاسمن", "هدیه",
    "ترانه", "کیمیا", "سپیده", "غزاله", "فرشته", "مهناز", "دلارام", "نازنین", "افسانه", "پگاه",
]
LAST_NAMES = [
    "احمدی", "محمدی", "حسینی", "رضایی", "موسوی", "کریمی", "جعفری", "صادقی", "قاسمی", "امینی",
    "باقری", "نوری", "شریفی", "کاظمی", "زارعی", "سلطانی", "فرهادی", "یوسفی", "عباسی", "هاشمی",
    "طاهری", "مرادی", "اکبری", "رحیمی", "خسروی", "بهرامی", "نجفی", "غفاری", "سعیدی", "مقدم",
    "دهقان", "افشار", "توکلی", "شکوهی", "میرزایی", "علوی", "پارسا", "رستمی", "صالحی", "نیکنام",
]
BLOOD_TYPES = ["A+", "A-", "B+", "B-", "AB+", "AB-", "O+", "O-"]
ALLERGIES = [
    "پنی‌سیلین", "لاتکس", "لیدوکائین", "آسپرین", "ید", "بی‌حسی موضعی", "سولفانامید",
]

INSURANCE_COMPANIES = ["تامین اجتماعی", "بیمه ایران", "بیمه دانا", "بیمه آسیا", "بیمه سینا"]

# name, category, min_cost, max_cost, duration_minutes, uses_tooth, description
SERVICES = [
    ("معاینه و تشخیص", "تشخیصی", 100_000, 200_000, 20, False, "معاینه اولیه و تشخیص وضعیت دهان و دندان"),
    ("رادیوگرافی پری‌اپیکال", "تشخیصی", 150_000, 250_000, 15, True, "عکس‌برداری موضعی از یک دندان"),
    ("رادیوگرافی پانورامیک", "تشخیصی", 300_000, 500_000, 20, False, "عکس‌برداری کامل از فک و دندان‌ها"),
    ("جرم‌گیری", "درمانی", 500_000, 800_000, 45, False, "پاک‌سازی جرم و پلاک دندانی"),
    ("فلوراید تراپی", "درمانی", 250_000, 400_000, 20, False, "پیشگیری از پوسیدگی با فلوراید"),
    ("فیشورسیلانت", "درمانی", 350_000, 600_000, 30, True, "پوشاندن شیارهای دندان برای پیشگیری"),
    ("پر کردن آمالگام", "درمانی", 800_000, 1_200_000, 45, True, "ترمیم دندان با آمالگام"),
    ("پر کردن کامپوزیت", "درمانی", 1_000_000, 1_500_000, 60, True, "ترمیم هم‌رنگ دندان با کامپوزیت"),
    ("ترمیم زیبایی کامپوزیت", "زیبایی", 1_500_000, 2_500_000, 60, True, "اصلاح فرم و رنگ دندان با کامپوزیت"),
    ("عصب‌کشی تک‌کاناله", "درمانی", 2_000_000, 2_800_000, 60, True, "درمان ریشه دندان تک‌کاناله"),
    ("عصب‌کشی دوکاناله", "درمانی", 2_500_000, 3_400_000, 75, True, "درمان ریشه دندان دوکاناله"),
    ("عصب‌کشی سه‌کاناله", "درمانی", 3_000_000, 4_000_000, 90, True, "درمان ریشه دندان سه‌کاناله"),
    ("کشیدن دندان ساده", "جراحی", 600_000, 1_000_000, 30, True, "خارج کردن دندان به روش ساده"),
    ("کشیدن دندان عقل نهفته", "جراحی", 3_000_000, 6_000_000, 90, True, "جراحی خارج کردن دندان عقل نهفته"),
    ("جراحی لثه", "جراحی", 4_000_000, 8_000_000, 90, False, "جراحی درمانی یا زیبایی لثه"),
    ("ایمپلنت دندان", "جراحی", 15_000_000, 30_000_000, 120, True, "کاشت پایه ایمپلنت در استخوان فک"),
    ("پیوند استخوان", "جراحی", 8_000_000, 15_000_000, 90, True, "بازسازی استخوان فک پیش از ایمپلنت"),
    ("روکش PFM", "درمانی", 3_000_000, 5_000_000, 60, True, "روکش فلز-سرامیک"),
    ("روکش زیرکونیا", "زیبایی", 6_000_000, 10_000_000, 60, True, "روکش تمام‌سرامیک زیرکونیا"),
    ("بریج سه واحدی", "درمانی", 9_000_000, 15_000_000, 90, True, "جایگزینی دندان از دست رفته با بریج"),
    ("لمینت سرامیکی", "زیبایی", 7_000_000, 12_000_000, 90, True, "روکش نازک سرامیکی سطح جلویی دندان"),
    ("بلیچینگ", "زیبایی", 2_000_000, 4_000_000, 60, False, "سفید کردن دندان در مطب"),
    ("پروتز کامل متحرک", "درمانی", 10_000_000, 18_000_000, 60, False, "دست دندان کامل متحرک"),
    ("ارتودنسی ثابت", "درمانی", 28_000_000, 56_000_000, 120, False, "بستن براکت و شروع درمان ارتودنسی ثابت"),
    ("ویزیت دوره‌ای ارتودنسی", "درمانی", 800_000, 4_000_000, 20, False, "کنترل و تنظیم دوره‌ای سیم ارتودنسی"),
]

# name, unit, unit_price, service categories that consume it
CONSUMABLES = [
    ("لیدوکائین ۲٪", "میلی‌لیتر", 45_000, ["جراحی", "درمانی"]),
    ("کامپوزیت A2", "گرم", 380_000, ["درمانی", "زیبایی"]),
    ("کامپوزیت A3", "گرم", 380_000, ["درمانی", "زیبایی"]),
    ("آمالگام کپسولی", "عدد", 120_000, ["درمانی"]),
    ("دستکش لاتکس", "عدد", 8_000, ["تشخیصی", "درمانی", "جراحی", "زیبایی"]),
    ("ماسک سه‌لایه", "عدد", 5_000, ["تشخیصی", "درمانی", "جراحی", "زیبایی"]),
    ("سرسوزن دندانپزشکی", "عدد", 25_000, ["جراحی", "درمانی"]),
    ("نخ بخیه", "عدد", 180_000, ["جراحی"]),
    ("گاز استریل", "بسته", 40_000, ["جراحی", "درمانی"]),
    ("رول پنبه", "بسته", 30_000, ["تشخیصی", "درمانی", "جراحی", "زیبایی"]),
    ("اسید اچ فسفریک", "میلی‌لیتر", 60_000, ["درمانی", "زیبایی"]),
    ("باندینگ", "میلی‌لیتر", 250_000, ["درمانی", "زیبایی"]),
    ("سیلر کانال ریشه", "گرم", 320_000, ["درمانی"]),
    ("گوتاپرکا", "عدد", 90_000, ["درمانی"]),
    ("فایل روتاری", "عدد", 450_000, ["درمانی"]),
    ("ماتریس نواری", "عدد", 15_000, ["درمانی"]),
    ("وج چوبی", "عدد", 6_000, ["درمانی"]),
    ("سمان گلاس‌آینومر", "گرم", 210_000, ["درمانی"]),
    ("سمان رزینی", "گرم", 340_000, ["درمانی", "زیبایی"]),
    ("آلژینات قالب‌گیری", "گرم", 55_000, ["درمانی", "زیبایی"]),
    ("گچ دندانپزشکی", "گرم", 12_000, ["درمانی"]),
    ("ژل بلیچینگ", "میلی‌لیتر", 520_000, ["زیبایی"]),
    ("براکت ارتودنسی", "عدد", 150_000, ["درمانی"]),
    ("وایر ارتودنسی", "عدد", 220_000, ["درمانی"]),
    ("کش ارتودنسی", "بسته", 35_000, ["درمانی"]),
    ("فلوراید ورنیش", "میلی‌لیتر", 95_000, ["درمانی"]),
    ("فیشورسیلانت رزینی", "میلی‌لیتر", 280_000, ["درمانی"]),
    ("محلول ضدعفونی سطوح", "میلی‌لیتر", 18_000, ["تشخیصی", "درمانی", "جراحی", "زیبایی"]),
    ("ساکشن تیپ یکبارمصرف", "عدد", 9_000, ["تشخیصی", "درمانی", "جراحی", "زیبایی"]),
    ("فیلم رادیوگرافی", "عدد", 70_000, ["تشخیصی"]),
]

SUPPLIERS = ["پخش دنداطب", "بازرگانی مروارید", "تجهیزات پارس دنت", "شرکت آریا مد", "دنتال سنتر ایران"]

# Treatment plan templates: (label, dentist specialty, weight, gap_days, service names)
# "+N" suffix means the service repeats a random number of times.
PLAN_TEMPLATES = [
    ("ترمیمی", "عمومی", 26, (10, 35),
     ["معاینه و تشخیص", "جرم‌گیری", "پر کردن کامپوزیت+3"]),
    ("درمان ریشه", "عمومی", 20, (7, 25),
     ["معاینه و تشخیص", "رادیوگرافی پری‌اپیکال", "عصب‌کشی دوکاناله", "روکش PFM"]),
    ("کودکان", "کودکان", 12, (14, 45),
     ["معاینه و تشخیص", "فلوراید تراپی", "فیشورسیلانت+2", "پر کردن آمالگام+1"]),
    ("جراحی", "جراح", 12, (10, 30),
     ["معاینه و تشخیص", "رادیوگرافی پانورامیک", "کشیدن دندان عقل نهفته+1"]),
    ("ایمپلنت", "ایمپلنت", 10, (20, 60),
     ["معاینه و تشخیص", "رادیوگرافی پانورامیک", "پیوند استخوان", "ایمپلنت دندان", "روکش زیرکونیا"]),
    ("زیبایی", "عمومی", 9, (14, 40),
     ["معاینه و تشخیص", "جرم‌گیری", "بلیچینگ", "لمینت سرامیکی+2"]),
    ("پروتز", "عمومی", 5, (14, 40),
     ["معاینه و تشخیص", "رادیوگرافی پانورامیک", "پروتز کامل متحرک"]),
    ("ارتودنسی", "ارتودنسی", 6, (21, 28), None),  # built separately, cost-driven
]
ORTHO_PLAN_MIN, ORTHO_PLAN_MAX = 40_000_000, 80_000_000

MAX_PLAN_SPAN = 300  # days; keeps all sessions inside the last 12 months
PLAN_STATUS_SUSPENDED_RATE = 0.05
FILLER_SERVICE = "پر کردن کامپوزیت"


def rint(a, b):
    return random.randint(a, b)


def money(lo, hi):
    """Random price rounded to the nearest 10,000 تومان, kept inside [lo, hi]."""
    v = round(random.uniform(lo, hi) / 10_000) * 10_000
    return int(min(max(v, lo), hi))


def national_code():
    """Iranian national code: 9 random digits + control digit (mod-11 checksum)."""
    while True:
        digits = [rint(0, 9) for _ in range(9)]
        if len(set(digits)) == 1:  # repdigit codes are invalid
            continue
        s = sum(d * (10 - i) for i, d in enumerate(digits))
        r = s % 11
        digits.append(r if r < 2 else 11 - r)
        return "".join(map(str, digits))


def valid_national_code(code):
    if not re.fullmatch(r"\d{10}", code) or len(set(code)) == 1:
        return False
    s = sum(int(d) * (10 - i) for i, d in enumerate(code[:9]))
    r = s % 11
    return int(code[9]) == (r if r < 2 else 11 - r)


def phone():
    return "09" + "".join(str(rint(0, 9)) for _ in range(9))


def d(x):
    return x.strftime("%Y-%m-%d")


def dt(x):
    return x.strftime("%Y-%m-%d %H:%M:%S")


def days_ago(lo, hi):
    return TODAY - timedelta(days=rint(lo, hi))


# ---------------------------------------------------------------- reference data

def gen_insurance():
    rows = []
    for i, company in enumerate(INSURANCE_COMPANIES, start=1):
        rows.append({
            "insurance_id": i,
            "company_name": company,
            "policy_number": f"POL-{1000 + i * 137}",
            "coverage_percentage": f"{random.choice([15, 20, 25, 30, 35, 40]):.2f}",
            # One company's contract has already lapsed, so the "not expired"
            # branch of the invoice rule is actually exercised by the data.
            "expiry_date": d(TODAY - timedelta(days=200) if i == 5
                             else TODAY + timedelta(days=rint(120, 900))),
        })
    return rows


def gen_dentists():
    specialties = ["عمومی", "عمومی", "عمومی", "ارتودنسی", "جراح", "جراح", "کودکان", "ایمپلنت"]
    rows = []
    for i, spec in enumerate(specialties, start=1):
        male = random.random() < 0.6
        rows.append({
            "dentist_id": i,
            "first_name": random.choice(MALE_FIRST if male else FEMALE_FIRST),
            "last_name": random.choice(LAST_NAMES),
            "specialty": spec,
            "license_number": f"MD-{10000 + i * 373}",
            "hire_date": d(days_ago(400, 3600)),
            "commission_rate": f"{random.choice([25, 30, 35, 40, 45]):.2f}",
        })
    return rows


def gen_staff():
    roles = ["پذیرش", "پذیرش", "دستیار", "دستیار", "دستیار", "حسابدار"]
    salaries = {"پذیرش": (14_000_000, 20_000_000),
                "دستیار": (16_000_000, 24_000_000),
                "حسابدار": (25_000_000, 35_000_000)}
    rows = []
    for i, role in enumerate(roles, start=1):
        female = random.random() < 0.7
        lo, hi = salaries[role]
        rows.append({
            "staff_id": i,
            "first_name": random.choice(FEMALE_FIRST if female else MALE_FIRST),
            "last_name": random.choice(LAST_NAMES),
            "role": role,
            "phone": phone(),
            "hire_date": d(days_ago(200, 2500)),
            "salary": money(lo, hi),
        })
    return rows


def gen_services():
    rows = []
    for i, (name, cat, lo, hi, dur, _tooth, desc) in enumerate(SERVICES, start=1):
        rows.append({
            "service_id": i,
            "name": name,
            "category": cat,
            "base_price": int(round((lo + hi) / 2 / 50_000) * 50_000),
            "duration_minutes": dur,
            "description": desc,
        })
    return rows


def gen_consumables():
    rows = []
    for i, (name, unit, price, _cats) in enumerate(CONSUMABLES, start=1):
        min_level = round(random.uniform(20, 200), 2)
        rows.append({
            "consumable_id": i,
            "name": name,
            "unit": unit,
            "stock_quantity": f"{round(min_level * random.uniform(0.6, 8.0), 2):.2f}",
            "min_stock_level": f"{min_level:.2f}",
            "unit_price": price,
            "supplier": random.choice(SUPPLIERS),
        })
    return rows


def gen_patients(insurance):
    rows, used_codes = [], set()
    for i in range(1, N_PATIENTS + 1):
        code = national_code()
        while code in used_codes:
            code = national_code()
        used_codes.add(code)

        female = random.random() < 0.52
        age = rint(3, 95) if random.random() < 0.08 else rint(6, 70)  # long tail, mostly adults
        birth = TODAY - timedelta(days=age * 365 + rint(0, 364))
        # Registered after birth and within the last 3 years.
        earliest = max(birth + timedelta(days=1), TODAY - timedelta(days=1095))
        reg = earliest + timedelta(days=rint(0, max((TODAY - earliest).days, 0)))

        has_ins = random.random() < 0.75
        rows.append({
            "patient_id": i,
            "national_code": code,
            "first_name": random.choice(FEMALE_FIRST if female else MALE_FIRST),
            "last_name": random.choice(LAST_NAMES),
            "birth_date": d(birth),
            "gender": "زن" if female else "مرد",
            "phone": phone(),
            "address": fake.address().replace("\n", "، ")[:255],
            "blood_type": random.choice(BLOOD_TYPES) if random.random() < 0.7 else "",
            "allergies": random.choice(ALLERGIES) if random.random() < 0.18 else "",
            "insurance_id": random.choice(insurance)["insurance_id"] if has_ins else "",
            "registration_date": d(reg),
        })
    return rows


# ---------------------------------------------------------------- scheduling

class Scheduler:
    """Hands out free (slot, chair) pairs, keeping one dentist and one chair
    from being double-booked in the same 30-minute slot."""

    def __init__(self):
        self.by_dentist = defaultdict(set)  # dentist_id -> {(date, slot)}
        self.by_chair = defaultdict(set)    # chair -> {(date, slot)}

    def book(self, dentist_id, target: date, search_days=45):
        """Return (datetime, chair) at or after `target`, skipping Fridays."""
        for offset in range(search_days):
            day = target + timedelta(days=offset)
            if day.weekday() == 4:  # Friday: clinic closed
                continue
            slots = SLOTS[:]
            random.shuffle(slots)
            for slot in slots:
                key = (day, slot)
                if key in self.by_dentist[dentist_id]:
                    continue
                free = [c for c in CHAIRS if key not in self.by_chair[c]]
                if not free:
                    continue
                chair = random.choice(free)
                self.by_dentist[dentist_id].add(key)
                self.by_chair[chair].add(key)
                return datetime.combine(day, slot), chair
        raise RuntimeError(f"no free slot near {target} for dentist {dentist_id}")


def expand_template(services_spec):
    """Turn ["پر کردن کامپوزیت+3", ...] into a flat list of service names."""
    out = []
    for item in services_spec:
        if "+" in item:
            name, extra = item.rsplit("+", 1)
            out.extend([name] * (1 + rint(0, int(extra))))
        else:
            out.append(item)
    return out


def build_plan_shapes():
    """Pick a template per plan and return service-name lists totalling
    exactly N_SESSIONS rows across N_PLANS plans."""
    labels = [t[0] for t in PLAN_TEMPLATES]
    weights = [t[2] for t in PLAN_TEMPLATES]
    shapes = []
    for _ in range(N_PLANS):
        label = random.choices(labels, weights=weights, k=1)[0]
        if label == "ارتودنسی":
            names = (["معاینه و تشخیص", "رادیوگرافی پانورامیک", "ارتودنسی ثابت"]
                     + ["ویزیت دوره‌ای ارتودنسی"] * rint(6, 11))
        else:
            spec = next(t[4] for t in PLAN_TEMPLATES if t[0] == label)
            names = expand_template(spec)
        shapes.append([label, names])

    # Nudge to the exact session budget by padding/trimming non-ortho plans.
    def total():
        return sum(len(s[1]) for s in shapes)

    guard = 0
    while total() != N_SESSIONS and guard < 100_000:
        guard += 1
        i = rint(0, N_PLANS - 1)
        label, names = shapes[i]
        if label == "ارتودنسی":
            continue
        if total() < N_SESSIONS and len(names) < 9:
            names.append(FILLER_SERVICE)
        elif total() > N_SESSIONS and len(names) > 2:
            names.pop()
    assert total() == N_SESSIONS, f"session budget off: {total()}"
    return shapes


def ortho_costs(n_visits, exam, pano):
    """Split a 40M–80M ortho plan across bonding + periodic visits so the
    plan total lands inside the required range by construction."""
    target = money(ORTHO_PLAN_MIN, ORTHO_PLAN_MAX)
    bonding = int(round(target * random.uniform(0.66, 0.74) / 10_000) * 10_000)
    rest = target - bonding - exam - pano
    per = int(round(rest / n_visits / 10_000) * 10_000)
    visits = [per] * n_visits
    visits[-1] += rest - per * n_visits  # absorb rounding drift
    return bonding, visits


def gen_plans_sessions_appointments(patients, dentists, staff, services):
    """Build treatment plans, their sessions, and every appointment.

    Sessions are placed first (each one owns a انجام‌شده appointment inside its
    plan window); the remaining 600 appointments are filled in afterwards.
    """
    svc_by_name = {s["name"]: s for s in services}
    svc_meta = {name: (lo, hi, tooth) for name, _c, lo, hi, _d, tooth, _desc in SERVICES}
    by_specialty = defaultdict(list)
    for de in dentists:
        by_specialty[de["specialty"]].append(de["dentist_id"])
    reg_date = {p["patient_id"]: datetime.strptime(p["registration_date"], "%Y-%m-%d").date()
                for p in patients}
    receptionists = [s["staff_id"] for s in staff if s["role"] == "پذیرش"]

    sched = Scheduler()
    plans, sessions, appointments = [], [], []
    plan_id = session_id = appt_id = 0

    for label, names in build_plan_shapes():
        plan_id += 1
        gap_lo, gap_hi = next(t[3] for t in PLAN_TEMPLATES if t[0] == label)
        specialty = next(t[1] for t in PLAN_TEMPLATES if t[0] == label)
        dentist_id = random.choice(by_specialty[specialty])

        gaps = [rint(gap_lo, gap_hi) for _ in range(len(names) - 1)]
        span = sum(gaps)
        if span > MAX_PLAN_SPAN:  # keep every plan inside the last 12 months
            gaps = [max(3, g * MAX_PLAN_SPAN // span) for g in gaps]
            span = sum(gaps)
        # Start early enough that every session lands on or before today
        # (+10 days of slack for slots pushed forward by a full schedule).
        start = TODAY - timedelta(days=rint(span + 10, max(span + 10, min(span + 70, 355))))

        # Patient must already be registered when the plan starts.
        eligible = [pid for pid in random.sample(range(1, N_PATIENTS + 1), 60)
                    if reg_date[pid] < start]
        if not eligible:
            eligible = [pid for pid in range(1, N_PATIENTS + 1) if reg_date[pid] < start]
        patient_id = random.choice(eligible)

        # Costs first: ortho is allocated from a plan-level target.
        if label == "ارتودنسی":
            n_visits = sum(1 for n in names if n == "ویزیت دوره‌ای ارتودنسی")
            exam = money(*svc_meta["معاینه و تشخیص"][:2])
            pano = money(*svc_meta["رادیوگرافی پانورامیک"][:2])
            bonding, visits = ortho_costs(n_visits, exam, pano)
            costs, vi = [], 0
            for n in names:
                if n == "معاینه و تشخیص":
                    costs.append(exam)
                elif n == "رادیوگرافی پانورامیک":
                    costs.append(pano)
                elif n == "ارتودنسی ثابت":
                    costs.append(bonding)
                else:
                    costs.append(visits[vi])
                    vi += 1
        else:
            costs = [money(*svc_meta[n][:2]) for n in names]

        # Place each session on its own appointment slot.
        session_rows, cursor = [], start
        for idx, name in enumerate(names):
            if idx:
                cursor += timedelta(days=gaps[idx - 1])
            when, chair = sched.book(dentist_id, cursor)
            cursor = when.date()

            appt_id += 1
            appointments.append({
                "appointment_id": appt_id,
                "patient_id": patient_id,
                "dentist_id": dentist_id,
                "created_by_staff_id": random.choice(receptionists) if random.random() < 0.95 else "",
                "scheduled_datetime": dt(when),
                "status": "انجام‌شده",
                "chair_number": chair,
            })

            session_id += 1
            session_rows.append({
                "session_id": session_id,
                "plan_id": plan_id,
                "appointment_id": appt_id,
                "service_id": svc_by_name[name]["service_id"],
                "tooth_number": rint(1, 32) if svc_meta[name][2] else "",
                "session_date": dt(when),
                "actual_cost": costs[idx],
                "notes": random.choice([
                    "درمان طبق برنامه انجام شد.", "بیمار همکاری خوبی داشت.",
                    "نیاز به پیگیری در جلسه بعد.", "بی‌حسی موضعی تزریق شد.",
                    "توصیه به رعایت بهداشت دهان.", "",
                ]),
            })
        sessions.extend(session_rows)

        last_session = max(datetime.strptime(s["session_date"], "%Y-%m-%d %H:%M:%S").date()
                           for s in session_rows)
        est_end = last_session + timedelta(days=rint(0, 90))
        if est_end > TODAY:
            status = "لغو" if random.random() < 0.04 else "فعال"
        else:
            status = "معلق" if random.random() < PLAN_STATUS_SUSPENDED_RATE else "تکمیل‌شده"

        plans.append({
            "plan_id": plan_id,
            "patient_id": patient_id,
            "dentist_id": dentist_id,
            "start_date": d(start),
            "estimated_end_date": d(est_end),
            # Estimate drifts from what was actually billed, as it would in reality.
            "total_estimated_cost": int(round(sum(costs) * random.uniform(0.9, 1.1) / 10_000) * 10_000),
            "status": status,
        })

    # Remaining appointments carry no session: cancelled / no-show / future booking.
    all_dentists = [de["dentist_id"] for de in dentists]
    for status, count in STATUS_MIX.items():
        if status == "انجام‌شده":
            continue
        for _ in range(count):
            dentist_id = random.choice(all_dentists)
            if status == "رزرو":
                target = TODAY + timedelta(days=rint(1, 45))
                patient_id = rint(1, N_PATIENTS)
            else:
                target = days_ago(1, 350)
                patient_id = random.choice([p for p in random.sample(range(1, N_PATIENTS + 1), 40)
                                            if reg_date[p] < target] or [1])
            if reg_date[patient_id] >= target:
                patient_id = min(reg_date, key=lambda k: reg_date[k])
            when, chair = sched.book(dentist_id, target)
            appt_id += 1
            appointments.append({
                "appointment_id": appt_id,
                "patient_id": patient_id,
                "dentist_id": dentist_id,
                "created_by_staff_id": random.choice(receptionists) if random.random() < 0.95 else "",
                "scheduled_datetime": dt(when),
                "status": status,
                "chair_number": chair,
            })

    appointments.sort(key=lambda a: a["scheduled_datetime"])
    for new_id, a in enumerate(appointments, start=1):
        a["_new_id"] = new_id
    remap = {a["appointment_id"]: a["_new_id"] for a in appointments}
    for a in appointments:
        a["appointment_id"] = a.pop("_new_id")
    for s in sessions:
        s["appointment_id"] = remap[s["appointment_id"]]
    return plans, sessions, appointments


# ---------------------------------------------------------------- billing

def gen_invoices(plans, sessions, patients, insurance):
    ins_by_id = {i["insurance_id"]: i for i in insurance}
    pat_by_id = {p["patient_id"]: p for p in patients}
    totals, last_date = defaultdict(int), {}
    for s in sessions:
        totals[s["plan_id"]] += s["actual_cost"]
        sd = datetime.strptime(s["session_date"], "%Y-%m-%d %H:%M:%S").date()
        last_date[s["plan_id"]] = max(last_date.get(s["plan_id"], sd), sd)

    rows = []
    for i, plan in enumerate(plans, start=1):
        total = totals[plan["plan_id"]]
        issue = last_date[plan["plan_id"]]
        patient = pat_by_id[plan["patient_id"]]

        covered = 0
        if patient["insurance_id"] != "":
            ins = ins_by_id[patient["insurance_id"]]
            if datetime.strptime(ins["expiry_date"], "%Y-%m-%d").date() >= issue:
                covered = int(total * float(ins["coverage_percentage"]) / 100)

        rows.append({
            "invoice_id": i,
            "patient_id": plan["patient_id"],
            "plan_id": plan["plan_id"],
            "issue_date": d(issue),
            "total_amount": total,
            "insurance_covered": covered,
            "patient_share": total - covered,
            "status": "",  # set once payments are known
        })
    return rows


def gen_payments(invoices):
    """Spread exactly N_PAYMENTS payments over the invoices and set each
    invoice status from what was actually paid."""
    # 60 unpaid + 120x1 + 180x2 + 40x3 = 400 invoices / 600 payments
    counts = [0] * 60 + [1] * 120 + [2] * 180 + [3] * 40
    random.shuffle(counts)
    assert len(counts) == len(invoices) and sum(counts) == N_PAYMENTS

    rows, pid = [], 0
    for inv, k in zip(invoices, counts):
        share = inv["patient_share"]
        if k == 0 or share <= 0:
            inv["status"] = "معوق" if share > 0 else "پرداخت‌شده"
            continue

        full = random.random() < 0.7
        target = share if full else int(share * random.uniform(0.35, 0.85) / 10_000) * 10_000
        target = max(target, 10_000)

        parts = [int(target / k / 10_000) * 10_000] * k
        parts[-1] += target - sum(parts)

        issue = datetime.strptime(inv["issue_date"], "%Y-%m-%d").date()
        pay_day = issue
        for n, amount in enumerate(parts):
            pay_day = min(pay_day + timedelta(days=0 if n == 0 else rint(20, 60)), TODAY)
            method = random.choices(["کارت", "نقد", "چک", "بیمه"], weights=[60, 25, 10, 5])[0]
            pid += 1
            rows.append({
                "payment_id": pid,
                "invoice_id": inv["invoice_id"],
                "amount": amount,
                "payment_date": d(pay_day),
                "method": method,
                "reference_number": "" if method == "نقد" else f"REF-{rint(10**7, 10**8 - 1)}",
            })
        inv["status"] = "پرداخت‌شده" if sum(parts) >= share else "بخشی"

    assert len(rows) == N_PAYMENTS, len(rows)
    return rows


def gen_usage(sessions, services, consumables):
    """Attach consumables to sessions, matched to the service category."""
    cat_by_service = {s["service_id"]: s["category"] for s in services}
    pool = defaultdict(list)
    for i, (_n, _u, _p, cats) in enumerate(CONSUMABLES, start=1):
        for c in cats:
            pool[c].append(i)

    extras = [0] * len(sessions)
    for _ in range(N_USAGE - len(sessions)):
        extras[rint(0, len(sessions) - 1)] += 1

    rows, uid = [], 0
    for s, extra in zip(sessions, extras):
        candidates = pool[cat_by_service[s["service_id"]]]
        want = min(1 + extra, len(candidates))
        for cid in random.sample(candidates, want):
            uid += 1
            rows.append({
                "usage_id": uid,
                "consumable_id": cid,
                "session_id": s["session_id"],
                "quantity_used": f"{round(random.uniform(0.5, 6.0), 2):.2f}",
                "usage_date": s["session_date"],
            })
    # sample() caps at the pool size, so top up to hit the target exactly.
    while len(rows) < N_USAGE:
        s = random.choice(sessions)
        cid = random.choice(pool[cat_by_service[s["service_id"]]])
        uid += 1
        rows.append({
            "usage_id": uid,
            "consumable_id": cid,
            "session_id": s["session_id"],
            "quantity_used": f"{round(random.uniform(0.5, 6.0), 2):.2f}",
            "usage_date": s["session_date"],
        })
    return rows[:N_USAGE]


# ---------------------------------------------------------------- output

def write_csv(name, rows):
    path = DATA_DIR / name
    with path.open("w", newline="", encoding="utf-8-sig") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)
    return path


def export_site_data(t):
    """Emit the compact JSON the clinic website renders from.

    The public site reads its doctor roster, service catalogue and headline
    numbers from here, so it always reflects the real database instead of
    hardcoded marketing copy that silently drifts out of date.
    """
    def years(hire_date):
        return max((TODAY - datetime.strptime(hire_date, "%Y-%m-%d").date()).days // 365, 1)

    payload = {
        "generated_at": TODAY.isoformat(),
        "stats": {
            "patients": len(t["patients"]),
            "dentists": len(t["dentists"]),
            "services": len(t["services"]),
            "sessions_last_year": len(t["treatment_sessions"]),
            "appointments_last_year": len(t["appointments"]),
        },
        "dentists": [
            {
                "name": f"دکتر {d['first_name']} {d['last_name']}",
                "specialty": d["specialty"],
                "license_number": d["license_number"],
                "experience_years": years(d["hire_date"]),
            }
            for d in sorted(t["dentists"], key=lambda x: x["hire_date"])
        ],
        "services": [
            {
                "name": s["name"],
                "category": s["category"],
                "base_price": s["base_price"],
                "duration_minutes": s["duration_minutes"],
                "description": s["description"],
            }
            for s in t["services"]
        ],
        "insurance": [i["company_name"] for i in t["insurance"]
                      if datetime.strptime(i["expiry_date"], "%Y-%m-%d").date() >= TODAY],
    }
    SITE_DATA_PATH.parent.mkdir(parents=True, exist_ok=True)
    SITE_DATA_PATH.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return SITE_DATA_PATH


def validate(t):
    """Re-check every business rule against the generated rows.
    Returns (checks, violations)."""
    checks, bad = [], []

    def check(label, ok, detail=""):
        checks.append((label, ok, detail))
        if not ok:
            bad.append(f"{label}: {detail}")

    expected = {
        "insurance": 5, "patients": N_PATIENTS, "dentists": N_DENTISTS, "staff": N_STAFF,
        "services": N_SERVICES, "appointments": N_APPOINTMENTS, "treatment_plans": N_PLANS,
        "treatment_sessions": N_SESSIONS, "invoices": N_INVOICES, "payments": N_PAYMENTS,
        "consumables": N_CONSUMABLES, "consumable_usage": N_USAGE,
    }
    for k, n in expected.items():
        check(f"row count {k} == {n}", len(t[k]) == n, f"got {len(t[k])}")

    pats = {p["patient_id"]: p for p in t["patients"]}
    codes = [p["national_code"] for p in t["patients"]]
    check("national_code unique", len(set(codes)) == len(codes))
    check("national_code checksum valid", all(valid_national_code(c) for c in codes))
    check("phone = 09 + 9 digits",
          all(re.fullmatch(r"09\d{9}", p["phone"]) for p in t["patients"] + t["staff"]))

    ages = [(TODAY - datetime.strptime(p["birth_date"], "%Y-%m-%d").date()).days // 365
            for p in t["patients"]]
    check("patient age in 3..95", all(3 <= a <= 95 for a in ages),
          f"range {min(ages)}..{max(ages)}")

    appts = {a["appointment_id"]: a for a in t["appointments"]}
    bad_reg = [a["appointment_id"] for a in t["appointments"]
               if datetime.strptime(a["scheduled_datetime"], "%Y-%m-%d %H:%M:%S").date()
               <= datetime.strptime(pats[a["patient_id"]]["registration_date"], "%Y-%m-%d").date()]
    check("appointment after patient registration", not bad_reg, f"{len(bad_reg)} bad")

    times = [datetime.strptime(a["scheduled_datetime"], "%Y-%m-%d %H:%M:%S") for a in t["appointments"]]
    check("appointment hours 08:00-21:00, 30-min slots",
          all(8 <= x.hour <= 20 and x.minute in (0, 30) and x.second == 0 for x in times))

    mix = Counter(a["status"] for a in t["appointments"])
    check("status mix 80/8/5/7", mix == Counter(STATUS_MIX), str(dict(mix)))
    check("رزرو appointments are in the future",
          all(datetime.strptime(a["scheduled_datetime"], "%Y-%m-%d %H:%M:%S").date() > TODAY
              for a in t["appointments"] if a["status"] == "رزرو"))
    check("انجام‌شده / لغو / غایب appointments are not in the future",
          all(datetime.strptime(a["scheduled_datetime"], "%Y-%m-%d %H:%M:%S").date() <= TODAY
              for a in t["appointments"] if a["status"] != "رزرو"))
    check("past appointments within last 12 months",
          all((TODAY - datetime.strptime(a["scheduled_datetime"], "%Y-%m-%d %H:%M:%S").date()).days <= 366
              for a in t["appointments"] if a["status"] != "رزرو"))

    booked = Counter((a["dentist_id"], a["scheduled_datetime"]) for a in t["appointments"])
    check("no dentist double-booked", max(booked.values()) == 1)
    chairs = Counter((a["chair_number"], a["scheduled_datetime"]) for a in t["appointments"])
    check("no chair double-booked", max(chairs.values()) == 1)

    plans = {p["plan_id"]: p for p in t["treatment_plans"]}
    out_of_window = [s["session_id"] for s in t["treatment_sessions"]
                     if not (datetime.strptime(plans[s["plan_id"]]["start_date"], "%Y-%m-%d").date()
                             <= datetime.strptime(s["session_date"], "%Y-%m-%d %H:%M:%S").date()
                             <= datetime.strptime(plans[s["plan_id"]]["estimated_end_date"], "%Y-%m-%d").date())]
    check("session_date within plan window", not out_of_window, f"{len(out_of_window)} bad")

    sess_appts = [s["appointment_id"] for s in t["treatment_sessions"]]
    completed = {a["appointment_id"] for a in t["appointments"] if a["status"] == "انجام‌شده"}
    check("appointment_id unique in sessions", len(set(sess_appts)) == len(sess_appts))
    check("one session per انجام‌شده appointment", set(sess_appts) == completed,
          f"{len(completed ^ set(sess_appts))} mismatched")
    check("session_date == appointment datetime",
          all(s["session_date"] == appts[s["appointment_id"]]["scheduled_datetime"]
              for s in t["treatment_sessions"]))

    teeth = [s["tooth_number"] for s in t["treatment_sessions"] if s["tooth_number"] != ""]
    check("tooth_number in 1..32", all(1 <= x <= 32 for x in teeth))

    svc = {s["service_id"]: s["name"] for s in t["services"]}
    ranges = {name: (lo, hi) for name, _c, lo, hi, _d, _to, _de in SERVICES}
    off = [s["session_id"] for s in t["treatment_sessions"]
           if not ranges[svc[s["service_id"]]][0] <= s["actual_cost"] <= ranges[svc[s["service_id"]]][1]]
    check("actual_cost within service price range", not off, f"{len(off)} bad")

    ortho_plans = {s["plan_id"] for s in t["treatment_sessions"] if svc[s["service_id"]] == "ارتودنسی ثابت"}
    ortho_totals = defaultdict(int)
    for s in t["treatment_sessions"]:
        if s["plan_id"] in ortho_plans:
            ortho_totals[s["plan_id"]] += s["actual_cost"]
    check("ارتودنسی plan total in 40M..80M",
          all(ORTHO_PLAN_MIN <= v <= ORTHO_PLAN_MAX for v in ortho_totals.values()),
          f"{len(ortho_totals)} plans")

    plan_totals = defaultdict(int)
    for s in t["treatment_sessions"]:
        plan_totals[s["plan_id"]] += s["actual_cost"]
    ins = {i["insurance_id"]: i for i in t["insurance"]}
    bad_total = bad_cov = bad_share = 0
    for inv in t["invoices"]:
        if inv["total_amount"] != plan_totals[inv["plan_id"]]:
            bad_total += 1
        p = pats[inv["patient_id"]]
        exp_cov = 0
        if p["insurance_id"] != "":
            i = ins[p["insurance_id"]]
            if datetime.strptime(i["expiry_date"], "%Y-%m-%d").date() >= \
               datetime.strptime(inv["issue_date"], "%Y-%m-%d").date():
                exp_cov = int(inv["total_amount"] * float(i["coverage_percentage"]) / 100)
        if inv["insurance_covered"] != exp_cov:
            bad_cov += 1
        if inv["patient_share"] != inv["total_amount"] - inv["insurance_covered"]:
            bad_share += 1
    check("invoice.total_amount == SUM(session.actual_cost)", bad_total == 0, f"{bad_total} bad")
    check("insurance_covered == total x coverage% (active policy only)", bad_cov == 0, f"{bad_cov} bad")
    check("patient_share == total - insurance_covered", bad_share == 0, f"{bad_share} bad")
    check("invoice.plan_id unique",
          len({i["plan_id"] for i in t["invoices"]}) == len(t["invoices"]))

    paid = defaultdict(int)
    for p in t["payments"]:
        paid[p["invoice_id"]] += p["amount"]
    over = [i["invoice_id"] for i in t["invoices"] if paid[i["invoice_id"]] > i["total_amount"]]
    check("SUM(payments) <= invoice.total_amount", not over, f"{len(over)} over-paid")
    check("payment amounts positive", all(p["amount"] > 0 for p in t["payments"]))
    check("payment_date >= invoice.issue_date",
          all(p["payment_date"] >= next(i["issue_date"] for i in t["invoices"]
                                        if i["invoice_id"] == p["invoice_id"])
              for p in t["payments"]))

    check("quantity_used > 0", all(float(u["quantity_used"]) > 0 for u in t["consumable_usage"]))

    fks = [
        ("patients.insurance_id", [p["insurance_id"] for p in t["patients"] if p["insurance_id"] != ""],
         {i["insurance_id"] for i in t["insurance"]}),
        ("appointments.patient_id", [a["patient_id"] for a in t["appointments"]], set(pats)),
        ("appointments.dentist_id", [a["dentist_id"] for a in t["appointments"]],
         {x["dentist_id"] for x in t["dentists"]}),
        ("appointments.created_by_staff_id",
         [a["created_by_staff_id"] for a in t["appointments"] if a["created_by_staff_id"] != ""],
         {x["staff_id"] for x in t["staff"]}),
        ("treatment_plans.patient_id", [p["patient_id"] for p in t["treatment_plans"]], set(pats)),
        ("treatment_sessions.plan_id", [s["plan_id"] for s in t["treatment_sessions"]], set(plans)),
        ("treatment_sessions.service_id", [s["service_id"] for s in t["treatment_sessions"]], set(svc)),
        ("invoices.plan_id", [i["plan_id"] for i in t["invoices"]], set(plans)),
        ("payments.invoice_id", [p["invoice_id"] for p in t["payments"]],
         {i["invoice_id"] for i in t["invoices"]}),
        ("consumable_usage.session_id", [u["session_id"] for u in t["consumable_usage"]],
         {s["session_id"] for s in t["treatment_sessions"]}),
        ("consumable_usage.consumable_id", [u["consumable_id"] for u in t["consumable_usage"]],
         {c["consumable_id"] for c in t["consumables"]}),
    ]
    orphans = [n for n, vals, parent in fks if not set(vals) <= parent]
    check("all foreign keys resolve", not orphans, ", ".join(orphans))

    return checks, bad


def main():
    DATA_DIR.mkdir(exist_ok=True)

    insurance = gen_insurance()
    dentists = gen_dentists()
    staff = gen_staff()
    services = gen_services()
    consumables = gen_consumables()
    patients = gen_patients(insurance)
    plans, sessions, appointments = gen_plans_sessions_appointments(
        patients, dentists, staff, services)
    invoices = gen_invoices(plans, sessions, patients, insurance)
    payments = gen_payments(invoices)
    usage = gen_usage(sessions, services, consumables)

    tables = {
        "insurance": insurance,
        "patients": patients,
        "dentists": dentists,
        "staff": staff,
        "services": services,
        "appointments": appointments,
        "treatment_plans": plans,
        "treatment_sessions": sessions,
        "invoices": invoices,
        "payments": payments,
        "consumables": consumables,
        "consumable_usage": usage,
    }
    for name, rows in tables.items():
        write_csv(f"{name}.csv", rows)
    export_site_data(tables)

    checks, bad = validate(tables)

    print("=" * 64)
    print(f"  DENTAL CLINIC — DATA GENERATION SUMMARY   ({TODAY})")
    print("=" * 64)
    print("\nCSV files written to data/\n")
    for name, rows in tables.items():
        print(f"  {name + '.csv':<26} {len(rows):>6} rows")
    print(f"\n  {'clinic-data.json':<26}  -> website/app/  (site roster + catalogue)")

    print(f"\nBusiness rule checks ({len(checks)} total)\n")
    for label, ok, detail in checks:
        mark = "PASS" if ok else "FAIL"
        print(f"  [{mark}] {label}" + (f"  -> {detail}" if detail and not ok else ""))

    print("\n" + "-" * 64)
    if bad:
        print(f"VIOLATIONS FOUND: {len(bad)}")
        for b in bad:
            print(f"  ! {b}")
        raise SystemExit(1)
    print("VIOLATIONS FOUND: 0  — all business rules satisfied.")
    print("-" * 64)


if __name__ == "__main__":
    main()
