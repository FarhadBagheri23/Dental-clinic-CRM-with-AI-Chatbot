"""Password verification and session tokens.

The password hashes were written by seeder/seed.py using hashlib.scrypt in the
format `scrypt$N$r$p$salt_hex$hash_hex`. Parameters are embedded in the stored
value, so changing them later does not invalidate existing accounts.
"""

import hashlib
import hmac
import time

import jwt

from app.core.config import settings

# Verified in place of a real hash when the username does not exist, so a
# missing user costs roughly the same time as a wrong password — otherwise
# response latency enumerates usernames.
DUMMY_HASH = "scrypt$16384$8$1$" + "00" * 16 + "$" + "00" * 64

ALGORITHM = "HS256"


def verify_password(password: str, stored: str) -> bool:
    """Constant-time check of a password against a stored scrypt hash."""
    if not isinstance(stored, str):
        return False

    parts = stored.split("$")
    if len(parts) != 6 or parts[0] != "scrypt":
        return False
    _, n, r, p, salt_hex, hash_hex = parts

    try:
        expected = bytes.fromhex(hash_hex)
        actual = hashlib.scrypt(
            password.encode(),
            salt=bytes.fromhex(salt_hex),
            n=int(n),
            r=int(r),
            p=int(p),
            dklen=len(expected),
            maxmem=64 * 1024 * 1024,
        )
    except (ValueError, MemoryError):
        return False

    return hmac.compare_digest(actual, expected)


def create_token(user: dict) -> str:
    now = int(time.time())
    return jwt.encode(
        {
            "sub": user["username"],
            "name": user.get("display_name") or user["username"],
            "role": user.get("role") or "کاربر",
            "iat": now,
            "exp": now + settings.session_ttl_hours * 3600,
        },
        settings.session_secret,
        algorithm=ALGORITHM,
    )


def read_token(token: str | None) -> dict | None:
    """Claims for a valid, unexpired token, otherwise None."""
    if not token:
        return None
    try:
        return jwt.decode(token, settings.session_secret, algorithms=[ALGORITHM])
    except jwt.InvalidTokenError:
        return None
