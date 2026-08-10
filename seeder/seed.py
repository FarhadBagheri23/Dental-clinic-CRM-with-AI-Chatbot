#!/usr/bin/env python3
"""Load the generated clinic CSVs into MongoDB.

The CSVs stay the source of truth for *generation*; MongoDB is the runtime
database the CRM reads from. This job is idempotent — it drops and rebuilds
every collection, so re-running after regenerating data is always safe.

Env:
  MONGO_URL       mongodb://... connection string
  MONGO_DB        database name
  DATA_DIR        directory holding the 12 CSVs
  ADMIN_USERNAME  CRM login to create
  ADMIN_PASSWORD  CRM password to hash
"""

import csv
import hashlib
import os
import secrets
import sys
import time
from datetime import datetime
from pathlib import Path

from pymongo import ASCENDING, MongoClient
from pymongo.errors import ServerSelectionTimeoutError

MONGO_URL = os.environ.get("MONGO_URL", "mongodb://localhost:27017")
MONGO_DB = os.environ.get("MONGO_DB", "dental_clinic")
DATA_DIR = Path(os.environ.get("DATA_DIR", "/data"))
ADMIN_USERNAME = os.environ.get("ADMIN_USERNAME", "admin")
ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD", "")

# scrypt parameters. Node's crypto.scryptSync must be called with the same
# values or verification silently fails — keep these two in sync with
# website/lib/auth.js.
SCRYPT_N, SCRYPT_R, SCRYPT_P, SCRYPT_DKLEN = 16384, 8, 1, 64


def _int(v):
    return None if v == "" else int(v)


def _float(v):
    return None if v == "" else float(v)


def _str(v):
    return None if v == "" else v


def _date(v):
    return None if v == "" else datetime.strptime(v, "%Y-%m-%d")


def _dt(v):
    return None if v == "" else datetime.strptime(v, "%Y-%m-%d %H:%M:%S")


# Explicit per-column types. Inferring would corrupt the data: national_code
# "0079542193" and phone "09123345567" are strings that look like integers.
SCHEMA = {
    "insurance": {
        "insurance_id": _int, "company_name": _str, "policy_number": _str,
        "coverage_percentage": _float, "expiry_date": _date,
    },
    "patients": {
        "patient_id": _int, "national_code": _str, "first_name": _str,
        "last_name": _str, "birth_date": _date, "gender": _str, "phone": _str,
        "address": _str, "blood_type": _str, "allergies": _str,
        "insurance_id": _int, "registration_date": _date,
    },
    "dentists": {
        "dentist_id": _int, "first_name": _str, "last_name": _str,
        "specialty": _str, "license_number": _str, "hire_date": _date,
        "commission_rate": _float,
    },
    "staff": {
        "staff_id": _int, "first_name": _str, "last_name": _str, "role": _str,
        "phone": _str, "hire_date": _date, "salary": _int,
    },
    "services": {
        "service_id": _int, "name": _str, "category": _str, "base_price": _int,
        "duration_minutes": _int, "description": _str,
    },
    "appointments": {
        "appointment_id": _int, "patient_id": _int, "dentist_id": _int,
        "created_by_staff_id": _int, "scheduled_datetime": _dt, "status": _str,
        "chair_number": _int,
    },
    "treatment_plans": {
        "plan_id": _int, "patient_id": _int, "dentist_id": _int,
        "start_date": _date, "estimated_end_date": _date,
        "total_estimated_cost": _int, "status": _str,
    },
    "treatment_sessions": {
        "session_id": _int, "plan_id": _int, "appointment_id": _int,
        "service_id": _int, "tooth_number": _int, "session_date": _dt,
        "actual_cost": _int, "notes": _str,
    },
    "invoices": {
        "invoice_id": _int, "patient_id": _int, "plan_id": _int,
        "issue_date": _date, "total_amount": _int, "insurance_covered": _int,
        "patient_share": _int, "status": _str,
    },
    "payments": {
        "payment_id": _int, "invoice_id": _int, "amount": _int,
        "payment_date": _date, "method": _str, "reference_number": _str,
    },
    "consumables": {
        "consumable_id": _int, "name": _str, "unit": _str,
        "stock_quantity": _float, "min_stock_level": _float,
        "unit_price": _int, "supplier": _str,
    },
    "consumable_usage": {
        "usage_id": _int, "consumable_id": _int, "session_id": _int,
        "quantity_used": _float, "usage_date": _dt,
    },
}

# Indexes the CRM actually queries on — primary keys, foreign keys used for
# joins, and the date columns every report filters by.
INDEXES = {
    "patients": [("patient_id", True), ("national_code", True),
                 ("last_name", False), ("registration_date", False)],
    "insurance": [("insurance_id", True)],
    "dentists": [("dentist_id", True)],
    "staff": [("staff_id", True)],
    "services": [("service_id", True)],
    "appointments": [("appointment_id", True), ("patient_id", False),
                     ("dentist_id", False), ("scheduled_datetime", False),
                     ("status", False)],
    "treatment_plans": [("plan_id", True), ("patient_id", False),
                        ("dentist_id", False)],
    "treatment_sessions": [("session_id", True), ("plan_id", False),
                           ("appointment_id", True), ("service_id", False),
                           ("session_date", False)],
    "invoices": [("invoice_id", True), ("plan_id", True),
                 ("patient_id", False), ("issue_date", False),
                 ("status", False)],
    "payments": [("payment_id", True), ("invoice_id", False),
                 ("payment_date", False)],
    "consumables": [("consumable_id", True)],
    "consumable_usage": [("usage_id", True), ("consumable_id", False),
                         ("session_id", False)],
}


def hash_password(password):
    """scrypt hash in a format website/lib/auth.js can verify."""
    salt = secrets.token_bytes(16)
    dk = hashlib.scrypt(password.encode(), salt=salt, n=SCRYPT_N, r=SCRYPT_R,
                        p=SCRYPT_P, dklen=SCRYPT_DKLEN, maxmem=64 * 1024 * 1024)
    return f"scrypt${SCRYPT_N}${SCRYPT_R}${SCRYPT_P}${salt.hex()}${dk.hex()}"


def wait_for_mongo(client, timeout=60):
    deadline = time.time() + timeout
    while True:
        try:
            client.admin.command("ping")
            return
        except ServerSelectionTimeoutError:
            if time.time() > deadline:
                raise
            print("  waiting for mongodb ...", flush=True)
            time.sleep(2)


def load_collection(db, name, coercers):
    path = DATA_DIR / f"{name}.csv"
    if not path.exists():
        raise SystemExit(
            f"missing {path} — run scripts/generate_data.py before seeding")

    with path.open(encoding="utf-8-sig") as f:
        docs = []
        for row in csv.DictReader(f):
            doc = {}
            for col, raw in row.items():
                fn = coercers.get(col)
                if fn is None:
                    raise SystemExit(f"{name}.csv: unmapped column '{col}'")
                doc[col] = fn(raw.strip())
            docs.append(doc)

    db.drop_collection(name)
    if docs:
        db[name].insert_many(docs, ordered=False)

    for field, unique in INDEXES.get(name, []):
        db[name].create_index([(field, ASCENDING)], unique=unique)

    return len(docs)


def seed_admin(db):
    if not ADMIN_PASSWORD:
        raise SystemExit(
            "ADMIN_PASSWORD is not set — refusing to create a CRM account "
            "without a password. Set it in .env")
    db.drop_collection("users")
    db.users.insert_one({
        "username": ADMIN_USERNAME,
        "password_hash": hash_password(ADMIN_PASSWORD),
        "display_name": "مدیر سیستم",
        "role": "مدیر",
        "created_at": datetime.utcnow(),
    })
    db.users.create_index([("username", ASCENDING)], unique=True)


def main():
    client = MongoClient(MONGO_URL, serverSelectionTimeoutMS=5000)
    print(f"connecting to {MONGO_DB} ...", flush=True)
    wait_for_mongo(client)

    db = client[MONGO_DB]
    print("\nseeding collections")
    total = 0
    for name, coercers in SCHEMA.items():
        n = load_collection(db, name, coercers)
        total += n
        print(f"  {name:<22} {n:>6} documents", flush=True)

    seed_admin(db)
    print(f"\n  {'users':<22} {1:>6} document  (CRM login: {ADMIN_USERNAME})")
    print(f"\ntotal {total:,} documents across {len(SCHEMA)} collections")
    print("seed complete.")


if __name__ == "__main__":
    sys.exit(main())
