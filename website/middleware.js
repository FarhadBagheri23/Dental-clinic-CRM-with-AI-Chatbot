import { NextResponse } from "next/server";

// Import from ./lib/session (Web Crypto only) — ./lib/auth pulls in
// node:crypto and the Mongo driver, neither of which run in Edge.
import { SESSION_COOKIE, readSessionToken } from "./lib/session";

// Everything under /admin-panel requires a session except the login page.
// Guarding here means a newly added CRM page is protected by default —
// forgetting a per-page check cannot leak data.
export async function middleware(request) {
  const { pathname } = request.nextUrl;
  const isLogin = pathname === "/admin-panel";
  const session = await readSessionToken(request.cookies.get(SESSION_COOKIE)?.value);

  if (!session && !isLogin) {
    const url = request.nextUrl.clone();
    url.pathname = "/admin-panel";
    url.search = `?next=${encodeURIComponent(pathname)}`;
    return NextResponse.redirect(url);
  }

  if (session && isLogin) {
    const url = request.nextUrl.clone();
    url.pathname = "/admin-panel/dashboard";
    url.search = "";
    return NextResponse.redirect(url);
  }

  return NextResponse.next();
}

export const config = {
  matcher: ["/admin-panel", "/admin-panel/:path*"],
};
