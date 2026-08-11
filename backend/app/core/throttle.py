"""Failed-login throttling.

Without this a single account plus unlimited guesses is the whole panel: the
login endpoint answered twelve wrong passwords in a row with twelve plain
401s and no delay. scrypt costs ~100ms, but it runs in a threadpool, so it
does not even serialise attempts.

State lives in Mongo rather than in a process dict because the API runs
behind nginx and may be scaled to more than one worker — a per-process
counter would give an attacker one full budget per worker. The collection is
TTL-indexed, so expiry is the database's job and nothing needs sweeping.

ponytail: counts failures per (username, IP). Not a general-purpose rate
limiter — if other endpoints ever need one, that is the point to reach for
slowapi rather than to grow this.
"""

from dataclasses import dataclass
from datetime import UTC, datetime, timedelta

from motor.motor_asyncio import AsyncIOMotorDatabase

COLLECTION = "login_attempts"

MAX_FAILURES = 5
LOCKOUT_SECONDS = 15 * 60


@dataclass(frozen=True)
class Lockout:
    """A refusal to even check the password, and how long it lasts."""
    retry_after: int


async def ensure_indexes(db: AsyncIOMotorDatabase) -> None:
    """TTL index so expired attempt records delete themselves."""
    await db[COLLECTION].create_index("expires_at", expireAfterSeconds=0)
    await db[COLLECTION].create_index([("key", 1)], unique=True)


def _key(username: str, ip: str) -> str:
    # Both, so one attacker cannot lock a real user out of their own account
    # by guessing from elsewhere, and one IP cannot spray many usernames.
    return f"{username.lower()}|{ip}"


async def check(db: AsyncIOMotorDatabase, username: str, ip: str) -> Lockout | None:
    """The active lockout for this caller, or None if they may try."""
    row = await db[COLLECTION].find_one({"key": _key(username, ip)})
    if not row or row.get("failures", 0) < MAX_FAILURES:
        return None

    # Mongo returns datetimes without a timezone, and a naive value is read as
    # *local* time by anything that converts it. On a UTC+03:30 host that put
    # every expiry 3.5 hours in the past, so `remaining` was always negative
    # and the lockout never engaged — the endpoint kept answering 401 forever.
    expires = row["expires_at"]
    if expires.tzinfo is None:
        expires = expires.replace(tzinfo=UTC)

    remaining = int((expires - datetime.now(UTC)).total_seconds())
    if remaining <= 0:
        return None
    return Lockout(retry_after=remaining)


async def record_failure(db: AsyncIOMotorDatabase, username: str, ip: str) -> None:
    """Count one failed attempt and extend the window.

    The window restarts on every failure, so a patient attacker trying once a
    minute never accumulates a budget.
    """
    await db[COLLECTION].update_one(
        {"key": _key(username, ip)},
        {
            "$inc": {"failures": 1},
            "$set": {"expires_at": datetime.now(UTC) + timedelta(seconds=LOCKOUT_SECONDS)},
        },
        upsert=True,
    )


async def clear(db: AsyncIOMotorDatabase, username: str, ip: str) -> None:
    """Forget the failures for this caller — called on a successful login."""
    await db[COLLECTION].delete_one({"key": _key(username, ip)})
