// Edge-safe session tokens.
//
// middleware.js runs in the Edge runtime, which has no `node:crypto`. This
// module uses Web Crypto only, so the same code verifies sessions in both
// middleware (Edge) and server components (Node).

const SESSION_TTL_SECONDS = 60 * 60 * 8; // one working day
export const SESSION_COOKIE = "clinic_session";

const encoder = new TextEncoder();

function bytesToB64url(bytes) {
  let binary = "";
  for (const b of bytes) binary += String.fromCharCode(b);
  return btoa(binary).replace(/\+/g, "-").replace(/\//g, "_").replace(/=+$/, "");
}

function b64urlToBytes(value) {
  const base64 = value.replace(/-/g, "+").replace(/_/g, "/");
  const padded = base64 + "=".repeat((4 - (base64.length % 4)) % 4);
  return Uint8Array.from(atob(padded), (c) => c.charCodeAt(0));
}

function secretOrThrow() {
  const s = process.env.SESSION_SECRET;
  if (!s || s.length < 16) {
    throw new Error("SESSION_SECRET is missing or shorter than 16 characters");
  }
  return s;
}

async function hmacKey() {
  // Fail loudly. If this were swallowed by the catch in readSessionToken,
  // every valid session would silently read as invalid and users would be
  // stuck in a login loop with nothing in the logs.
  if (!globalThis.crypto?.subtle) {
    throw new Error(
      "Web Crypto is unavailable in this runtime — Node >= 19 or the Edge runtime is required",
    );
  }
  return crypto.subtle.importKey(
    "raw",
    encoder.encode(secretOrThrow()),
    { name: "HMAC", hash: "SHA-256" },
    false,
    ["sign", "verify"],
  );
}

export async function createSessionToken(user) {
  const claims = {
    sub: user.username,
    name: user.display_name ?? user.username,
    role: user.role ?? "کاربر",
    exp: Math.floor(Date.now() / 1000) + SESSION_TTL_SECONDS,
  };
  const body = bytesToB64url(encoder.encode(JSON.stringify(claims)));
  const sig = await crypto.subtle.sign("HMAC", await hmacKey(), encoder.encode(body));
  return `${body}.${bytesToB64url(new Uint8Array(sig))}`;
}

/** Returns the claims for a valid, unexpired token, otherwise null. */
export async function readSessionToken(token) {
  if (!token || !token.includes(".")) return null;
  const [body, mac] = token.split(".");
  if (!body || !mac) return null;

  // Resolved outside the try so configuration errors (missing SESSION_SECRET,
  // no Web Crypto) surface instead of being reported as "invalid token".
  const key = await hmacKey();

  let valid;
  try {
    // subtle.verify is constant-time, so this is not a timing oracle.
    // Only malformed base64 in the signature can throw here.
    valid = await crypto.subtle.verify("HMAC", key, b64urlToBytes(mac), encoder.encode(body));
  } catch {
    return null;
  }
  if (!valid) return null;

  try {
    const claims = JSON.parse(new TextDecoder().decode(b64urlToBytes(body)));
    if (!claims.exp || claims.exp < Math.floor(Date.now() / 1000)) return null;
    return claims;
  } catch {
    return null;
  }
}

export { SESSION_TTL_SECONDS };
