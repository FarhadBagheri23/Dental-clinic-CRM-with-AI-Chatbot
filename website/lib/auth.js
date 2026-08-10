// Node-only auth helpers (password hashing, cookies, DB lookup).
// Session token signing/verification lives in ./session.js so the Edge
// middleware can reuse it — do not import this file from middleware.

import { scrypt, timingSafeEqual } from "node:crypto";
import { promisify } from "node:util";
import { cookies } from "next/headers";

import { col } from "./mongo";
import {
  SESSION_COOKIE,
  SESSION_TTL_SECONDS,
  createSessionToken,
  readSessionToken,
} from "./session";

const scryptAsync = promisify(scrypt);

export { SESSION_COOKIE };

/**
 * Verify a `scrypt$N$r$p$salt$hash` string produced by seeder/seed.py.
 * Parameters are embedded in the stored value, so changing them later does
 * not invalidate existing accounts.
 */
export async function verifyPassword(password, stored) {
  if (typeof stored !== "string") return false;
  const [scheme, N, r, p, saltHex, hashHex] = stored.split("$");
  if (scheme !== "scrypt" || !hashHex) return false;

  try {
    const expected = Buffer.from(hashHex, "hex");
    const actual = await scryptAsync(password, Buffer.from(saltHex, "hex"), expected.length, {
      N: Number(N),
      r: Number(r),
      p: Number(p),
      maxmem: 64 * 1024 * 1024,
    });
    return actual.length === expected.length && timingSafeEqual(actual, expected);
  } catch {
    return false;
  }
}

export async function setSessionCookie(user) {
  cookies().set(SESSION_COOKIE, await createSessionToken(user), {
    httpOnly: true,
    sameSite: "lax",
    secure: process.env.NODE_ENV === "production",
    path: "/",
    maxAge: SESSION_TTL_SECONDS,
  });
}

export function clearSessionCookie() {
  cookies().delete(SESSION_COOKIE);
}

/** Current session claims, or null. Call from server components. */
export async function currentUser() {
  return readSessionToken(cookies().get(SESSION_COOKIE)?.value);
}

export async function authenticate(username, password) {
  const users = await col("users");
  const user = await users.findOne({ username: String(username ?? "").trim() });

  // Always run a hash comparison so a missing user and a wrong password cost
  // roughly the same time — otherwise response latency enumerates usernames.
  const stored =
    user?.password_hash ??
    "scrypt$16384$8$1$0000000000000000000000000000000000000000000000000000000000000000$00";
  const ok = await verifyPassword(String(password ?? ""), stored);

  return ok && user ? user : null;
}
