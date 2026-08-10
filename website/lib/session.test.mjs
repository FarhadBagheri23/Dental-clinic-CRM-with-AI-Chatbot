// Self-check for the session token format. No framework — run it directly:
//   SESSION_SECRET=$(openssl rand -hex 32) node lib/session.test.mjs
//
// Covers the properties that actually matter: a token round-trips, a tampered
// payload is rejected, a wrong key is rejected, and an expired token is
// rejected. If any of these regress, sessions become forgeable.

import assert from "node:assert/strict";

// Node >= 19 exposes Web Crypto as a global (as does the Edge runtime, where
// session.js also runs). Shim it so this test still runs on Node 18.
if (!globalThis.crypto) {
  globalThis.crypto = (await import("node:crypto")).webcrypto;
}

process.env.SESSION_SECRET ||= "0123456789abcdef0123456789abcdef";

const { createSessionToken, readSessionToken } = await import("./session.js");

const user = { username: "admin", display_name: "مدیر سیستم", role: "مدیر" };

// 1. round-trip
const token = await createSessionToken(user);
const claims = await readSessionToken(token);
assert.equal(claims.sub, "admin");
assert.equal(claims.name, "مدیر سیستم");
assert.equal(claims.role, "مدیر");
assert.ok(claims.exp > Math.floor(Date.now() / 1000));

// 2. tampered payload is rejected (privilege escalation attempt)
const [body, mac] = token.split(".");
const forgedBody = Buffer.from(
  JSON.stringify({ ...claims, sub: "attacker" }),
).toString("base64url");
assert.equal(await readSessionToken(`${forgedBody}.${mac}`), null);

// 3. tampered signature is rejected
assert.equal(await readSessionToken(`${body}.${"A".repeat(mac.length)}`), null);

// 4. a token signed with a different key is rejected
process.env.SESSION_SECRET = "ffffffffffffffffffffffffffffffff";
const otherModule = await import(`./session.js?v=${Date.now()}`);
assert.equal(await otherModule.readSessionToken(token), null);
process.env.SESSION_SECRET = "0123456789abcdef0123456789abcdef";

// 5. expired tokens are rejected
const expired = await import(`./session.js?v=${Date.now()}-exp`);
const realNow = Date.now;
Date.now = () => realNow() - 9 * 60 * 60 * 1000; // 9h ago, TTL is 8h
const staleToken = await expired.createSessionToken(user);
Date.now = realNow;
assert.equal(await expired.readSessionToken(staleToken), null);

// 6. malformed input never throws
for (const bad of [undefined, "", "no-dot", "a.b.c", "....", "%%%.%%%"]) {
  assert.equal(await readSessionToken(bad), null);
}

console.log("session.test.mjs — all 6 checks passed ✅");
