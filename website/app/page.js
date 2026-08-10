"use client";

import { useState } from "react";
import { Home, Services, Doctors, Booking } from "./sections";
import { CLINIC } from "../lib/config";

// The CRM lives at /admin-panel behind a login and is deliberately absent
// from the public navigation.
const TABS = [
  { id: "home", label: "خانه", Panel: Home },
  { id: "services", label: "خدمات و تعرفه‌ها", Panel: Services },
  { id: "doctors", label: "کادر درمان", Panel: Doctors },
  { id: "booking", label: "نوبت آنلاین", Panel: Booking },
];

function ToothMark({ className = "h-7 w-7" }) {
  return (
    <svg className={className} viewBox="0 0 24 24" fill="currentColor" aria-hidden="true">
      <path d="M12 2C9.6 2 8.6 3 7 3c-1.3 0-2-.5-3-.5C2.5 2.5 2 4 2 6.2c0 2.6.9 4 1.6 5.6.5 1.2.8 2.5 1 3.9.3 2 .5 4 1 5.4.3.8.8 1.1 1.4 1 .7-.1 1-.8 1.2-1.9.2-1.1.4-2.6.7-3.9.3-1.4.9-2.3 2.1-2.3s1.8.9 2.1 2.3c.3 1.3.5 2.8.7 3.9.2 1.1.5 1.8 1.2 1.9.6.1 1.1-.2 1.4-1 .5-1.4.7-3.4 1-5.4.2-1.4.5-2.7 1-3.9.7-1.6 1.6-3 1.6-5.6C22 4 21.5 2.5 20 2.5c-1 0-1.7.5-3 .5-1.6 0-2.6-1-5-1z" />
    </svg>
  );
}

export default function Page() {
  const [tab, setTab] = useState("home");
  const [menuOpen, setMenuOpen] = useState(false);
  const Active = TABS.find((t) => t.id === tab).Panel;

  const go = (id) => {
    setTab(id);
    setMenuOpen(false);
    if (typeof window !== "undefined") window.scrollTo({ top: 0, behavior: "smooth" });
  };

  return (
    <div className="flex min-h-screen flex-col">
      <header className="sticky top-0 z-30 border-b border-slate-200 bg-white/90 backdrop-blur">
        <div className="mx-auto max-w-6xl px-4">
          <div className="flex h-16 items-center justify-between gap-4">
            <button
              onClick={() => go("home")}
              className="flex shrink-0 items-center gap-2.5 text-brand-700"
            >
              <ToothMark />
              <span className="text-sm font-black leading-tight text-slate-900 sm:text-base">
                {CLINIC.short}
              </span>
            </button>

            <nav className="hidden items-center gap-1 lg:flex" aria-label="منوی اصلی">
              {TABS.map((t) => (
                <button
                  key={t.id}
                  onClick={() => go(t.id)}
                  aria-current={tab === t.id ? "page" : undefined}
                  className={`rounded-lg px-3.5 py-2 text-sm font-medium transition ${
                    tab === t.id
                      ? "bg-brand-50 text-brand-700"
                      : "text-slate-600 hover:bg-slate-100"
                  }`}
                >
                  {t.label}
                </button>
              ))}
            </nav>

            <div className="flex items-center gap-2">
              <a
                href={`tel:${CLINIC.phone}`}
                className="hidden rounded-xl bg-brand-600 px-4 py-2.5 text-sm font-bold text-white shadow-sm transition hover:bg-brand-700 sm:block"
              >
                {CLINIC.phone}
              </a>
              <button
                onClick={() => setMenuOpen((v) => !v)}
                aria-label="باز و بسته کردن منو"
                aria-expanded={menuOpen}
                className="rounded-lg p-2 text-slate-600 hover:bg-slate-100 lg:hidden"
              >
                <svg className="h-6 w-6" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24">
                  <path strokeLinecap="round" d={menuOpen ? "M6 18L18 6M6 6l12 12" : "M4 7h16M4 12h16M4 17h16"} />
                </svg>
              </button>
            </div>
          </div>

          {menuOpen ? (
            <nav className="border-t border-slate-200 py-2 lg:hidden" aria-label="منوی موبایل">
              {TABS.map((t) => (
                <button
                  key={t.id}
                  onClick={() => go(t.id)}
                  className={`block w-full rounded-lg px-4 py-3 text-right text-sm font-medium transition ${
                    tab === t.id ? "bg-brand-50 text-brand-700" : "text-slate-600 hover:bg-slate-100"
                  }`}
                >
                  {t.label}
                </button>
              ))}
            </nav>
          ) : null}
        </div>
      </header>

      <main className="mx-auto w-full max-w-6xl flex-1 px-4 py-10 sm:py-14">
        <Active go={go} />
      </main>

      <footer className="mt-10 border-t border-slate-200 bg-white">
        <div className="mx-auto grid max-w-6xl gap-10 px-4 py-12 sm:grid-cols-2 lg:grid-cols-4">
          <div className="sm:col-span-2 lg:col-span-1">
            <div className="mb-4 flex items-center gap-2.5 text-brand-700">
              <ToothMark className="h-6 w-6" />
              <span className="font-black text-slate-900">{CLINIC.short}</span>
            </div>
            <p className="text-sm leading-8 text-slate-600">
              ارائه خدمات جامع دندان‌پزشکی با کادری مجرب و تجهیزات روز، در محیطی آرام
              و ایمن.
            </p>
          </div>

          <div>
            <h3 className="mb-4 text-sm font-black text-slate-900">دسترسی سریع</h3>
            <ul className="space-y-2.5 text-sm text-slate-600">
              {TABS.map((t) => (
                <li key={t.id}>
                  <button onClick={() => go(t.id)} className="transition hover:text-brand-700">
                    {t.label}
                  </button>
                </li>
              ))}
            </ul>
          </div>

          <div>
            <h3 className="mb-4 text-sm font-black text-slate-900">ساعات کاری</h3>
            <ul className="space-y-2.5 text-sm leading-7 text-slate-600">
              <li>{CLINIC.hours}</li>
              <li className="text-rose-600">{CLINIC.closed}</li>
              <li className="pt-2 text-xs text-slate-400">
                پذیرش اورژانس با هماهنگی تلفنی
              </li>
            </ul>
          </div>

          <div>
            <h3 className="mb-4 text-sm font-black text-slate-900">تماس با ما</h3>
            <ul className="space-y-3 text-sm leading-7 text-slate-600">
              <li className="flex gap-2">
                <span aria-hidden="true">📍</span>
                <span>{CLINIC.address}</span>
              </li>
              <li className="flex gap-2">
                <span aria-hidden="true">📞</span>
                <a href={`tel:${CLINIC.phone}`} className="font-bold hover:text-brand-700">
                  {CLINIC.phone}
                </a>
              </li>
              <li className="flex gap-2">
                <span aria-hidden="true">✉️</span>
                <span dir="ltr">{CLINIC.email}</span>
              </li>
            </ul>
          </div>
        </div>

        <div className="border-t border-slate-200 py-5 text-center text-xs text-slate-500">
          © ۱۴۰۵ — تمامی حقوق برای {CLINIC.name} محفوظ است.
        </div>
      </footer>
    </div>
  );
}
