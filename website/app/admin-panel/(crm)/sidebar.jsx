"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useState } from "react";

import { logoutAction } from "../actions";

const NAV = [
  { href: "/admin-panel/dashboard", label: "داشبورد", icon: "📊" },
  { href: "/admin-panel/patients", label: "بیماران", icon: "👤" },
  { href: "/admin-panel/appointments", label: "نوبت‌ها", icon: "📅" },
  { href: "/admin-panel/invoices", label: "فاکتورها", icon: "🧾" },
  { href: "/admin-panel/inventory", label: "انبار", icon: "📦" },
];

export default function Sidebar({ user }) {
  const pathname = usePathname();
  const [open, setOpen] = useState(false);

  const items = NAV.map((n) => {
    const active = pathname === n.href;
    return (
      <Link
        key={n.href}
        href={n.href}
        onClick={() => setOpen(false)}
        aria-current={active ? "page" : undefined}
        className={`flex items-center gap-3 rounded-xl px-4 py-3 text-sm font-medium transition ${
          active ? "bg-brand-600 text-white shadow-sm" : "text-slate-300 hover:bg-slate-800 hover:text-white"
        }`}
      >
        <span aria-hidden="true">{n.icon}</span>
        {n.label}
      </Link>
    );
  });

  return (
    <>
      <div className="flex items-center justify-between border-b border-slate-800 bg-slate-900 px-4 py-3 lg:hidden">
        <span className="text-sm font-black text-white">پنل مدیریت</span>
        <button
          onClick={() => setOpen((v) => !v)}
          aria-label="منوی پنل"
          aria-expanded={open}
          className="rounded-lg p-2 text-slate-300 hover:bg-slate-800"
        >
          <svg className="h-5 w-5" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24">
            <path strokeLinecap="round" d={open ? "M6 18L18 6M6 6l12 12" : "M4 7h16M4 12h16M4 17h16"} />
          </svg>
        </button>
      </div>

      <aside
        className={`${open ? "block" : "hidden"} w-full shrink-0 bg-slate-900 lg:block lg:min-h-screen lg:w-64`}
      >
        <div className="sticky top-0 flex h-full flex-col p-4">
          <div className="mb-8 hidden items-center gap-2.5 px-2 pt-2 lg:flex">
            <span className="text-2xl" aria-hidden="true">🦷</span>
            <div>
              <div className="text-sm font-black text-white">پنل مدیریت</div>
              <div className="text-[11px] text-slate-400">کلینیک باقری طاهری</div>
            </div>
          </div>

          <nav className="space-y-1.5">{items}</nav>

          <div className="mt-auto space-y-3 border-t border-slate-800 pt-4">
            <div className="px-2">
              <div className="text-sm font-bold text-white">{user?.name}</div>
              <div className="text-[11px] text-slate-400">{user?.role}</div>
            </div>
            <Link
              href="/"
              className="block rounded-xl px-4 py-2.5 text-sm text-slate-300 transition hover:bg-slate-800 hover:text-white"
            >
              ← مشاهده سایت کلینیک
            </Link>
            <form action={logoutAction}>
              <button
                type="submit"
                className="w-full rounded-xl bg-slate-800 px-4 py-2.5 text-sm font-bold text-rose-300 transition hover:bg-rose-900/40"
              >
                خروج از حساب
              </button>
            </form>
          </div>
        </div>
      </aside>
    </>
  );
}
