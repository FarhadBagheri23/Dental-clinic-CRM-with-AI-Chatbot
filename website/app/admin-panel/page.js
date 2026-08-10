import Link from "next/link";

import LoginForm from "./login-form";

export const metadata = {
  title: "ورود به پنل مدیریت",
  robots: { index: false, follow: false },
};

export default function AdminLoginPage({ searchParams }) {
  return (
    <div className="flex min-h-screen items-center justify-center bg-slate-100 px-4 py-12">
      <div className="w-full max-w-md">
        <div className="mb-8 text-center">
          <div className="mx-auto mb-4 flex h-14 w-14 items-center justify-center rounded-2xl bg-brand-600 text-white shadow-lg">
            <svg className="h-7 w-7" viewBox="0 0 24 24" fill="currentColor" aria-hidden="true">
              <path d="M12 2C9.6 2 8.6 3 7 3c-1.3 0-2-.5-3-.5C2.5 2.5 2 4 2 6.2c0 2.6.9 4 1.6 5.6.5 1.2.8 2.5 1 3.9.3 2 .5 4 1 5.4.3.8.8 1.1 1.4 1 .7-.1 1-.8 1.2-1.9.2-1.1.4-2.6.7-3.9.3-1.4.9-2.3 2.1-2.3s1.8.9 2.1 2.3c.3 1.3.5 2.8.7 3.9.2 1.1.5 1.8 1.2 1.9.6.1 1.1-.2 1.4-1 .5-1.4.7-3.4 1-5.4.2-1.4.5-2.7 1-3.9.7-1.6 1.6-3 1.6-5.6C22 4 21.5 2.5 20 2.5c-1 0-1.7.5-3 .5-1.6 0-2.6-1-5-1z" />
            </svg>
          </div>
          <h1 className="text-xl font-black text-slate-900">پنل مدیریت کلینیک</h1>
          <p className="mt-2 text-sm text-slate-500">
            این بخش مخصوص کادر درمان و مدیریت است.
          </p>
        </div>

        <div className="rounded-2xl border border-slate-200 bg-white p-7 shadow-sm">
          <LoginForm next={searchParams?.next} />
        </div>

        <p className="mt-6 text-center text-xs text-slate-500">
          <Link href="/" className="transition hover:text-brand-700">
            ← بازگشت به سایت کلینیک
          </Link>
        </p>
      </div>
    </div>
  );
}
