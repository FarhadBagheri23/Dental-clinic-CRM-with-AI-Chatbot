"use server";

import { redirect } from "next/navigation";

import { authenticate, setSessionCookie, clearSessionCookie } from "../../lib/auth";

export async function loginAction(prevState, formData) {
  const username = formData.get("username");
  const password = formData.get("password");
  const next = formData.get("next");

  if (!username || !password) {
    return { error: "نام کاربری و رمز عبور را وارد کنید." };
  }

  let user;
  try {
    user = await authenticate(username, password);
  } catch {
    return { error: "اتصال به پایگاه داده برقرار نشد. لطفاً بعداً تلاش کنید." };
  }

  if (!user) {
    // Deliberately identical for unknown user and wrong password.
    return { error: "نام کاربری یا رمز عبور نادرست است." };
  }

  await setSessionCookie(user);
  redirect(next && next.startsWith("/admin-panel") ? next : "/admin-panel/dashboard");
}

export async function logoutAction() {
  clearSessionCookie();
  redirect("/admin-panel");
}
