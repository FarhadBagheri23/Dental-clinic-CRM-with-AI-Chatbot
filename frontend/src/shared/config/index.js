// Same-origin by default: Vite proxies /api in dev, nginx proxies it in
// production. Override only when pointing at a remote API.
export const API_BASE = import.meta.env.VITE_API_BASE ?? "/api";

export const CLINIC = {
  name: "کلینیک دندان‌پزشکی فرهاد باقری طاهری",
  short: "کلینیک باقری طاهری",
};

// Mirrors app/schemas/auth.py. Kept in sync deliberately: the client check is
// for fast feedback, the server check is the one that counts.
export const USERNAME_RE = /^[A-Za-z0-9._-]+$/;
export const PASSWORD_RE = /^[\x21-\x7E]+$/;
