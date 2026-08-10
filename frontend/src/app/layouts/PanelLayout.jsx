import { useState } from "react";
import { NavLink, Outlet } from "react-router-dom";

import { useAuth } from "@/features/auth/hooks/useAuth";
import { LogoLockup } from "@/shared/ui/Logo";

const NAV = [
  { to: "/dashboard", label: "داشبورد", d: "M4 13h6V4H4v9zm0 7h6v-5H4v5zm10 0h6V11h-6v9zm0-16v5h6V4h-6z" },
  { to: "/patients", label: "بیماران", d: "M12 12a4 4 0 100-8 4 4 0 000 8zm0 2c-4 0-8 2-8 4.5V21h16v-2.5c0-2.5-4-4.5-8-4.5z" },
  { to: "/appointments", label: "نوبت‌ها", d: "M7 2v3M17 2v3M3 9h18M5 5h14a2 2 0 012 2v12a2 2 0 01-2 2H5a2 2 0 01-2-2V7a2 2 0 012-2z" },
  { to: "/invoices", label: "فاکتورها", d: "M6 2h9l5 5v15H6V2zm8 1v5h5M9 13h7M9 17h7" },
  { to: "/inventory", label: "انبار", d: "M3 7l9-4 9 4v10l-9 4-9-4V7zm9 4l9-4m-9 4L3 7m9 4v10" },
];

function NavIcon({ d }) {
  return (
    <svg className="h-5 w-5 shrink-0" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.7" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
      <path d={d} />
    </svg>
  );
}

function NavItems({ onNavigate }) {
  return NAV.map((item) => (
    <NavLink
      key={item.to}
      to={item.to}
      onClick={onNavigate}
      className={({ isActive }) =>
        `flex items-center gap-3 rounded-xl px-3.5 py-2.5 text-sm font-medium transition-colors ${
          isActive
            ? "bg-brand-700 text-white shadow-card"
            : "text-ink-600 hover:bg-ink-100 hover:text-ink-900"
        }`
      }
    >
      <NavIcon d={item.d} />
      {item.label}
    </NavLink>
  ));
}

export function PanelLayout() {
  const { user, logout } = useAuth();
  const [menuOpen, setMenuOpen] = useState(false);

  return (
    <div className="min-h-dvh lg:flex">
      {/* Sidebar — a permanent rail on desktop, a collapsible sheet below lg. */}
      <aside className="shrink-0 border-ink-200 bg-white lg:sticky lg:top-0 lg:h-dvh lg:w-64 lg:border-l">
        <div className="flex items-center justify-between gap-4 border-b border-ink-200 px-5 py-4 lg:border-0">
          <LogoLockup />
          <button
            onClick={() => setMenuOpen((v) => !v)}
            aria-expanded={menuOpen}
            aria-label="باز و بسته کردن منو"
            className="rounded-lg p-2 text-ink-600 transition-colors hover:bg-ink-100 lg:hidden"
          >
            <svg className="h-6 w-6" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24">
              <path strokeLinecap="round" d={menuOpen ? "M6 18L18 6M6 6l12 12" : "M4 7h16M4 12h16M4 17h16"} />
            </svg>
          </button>
        </div>

        <nav
          aria-label="منوی اصلی"
          className={`flex-col gap-1 px-3 py-4 lg:flex ${menuOpen ? "flex border-b border-ink-200" : "hidden"}`}
        >
          <NavItems onNavigate={() => setMenuOpen(false)} />
        </nav>
      </aside>

      <div className="min-w-0 flex-1">
        <header className="sticky top-0 z-20 border-b border-ink-200 bg-white/85 backdrop-blur">
          <div className="flex items-center justify-end gap-3 px-5 py-3.5 sm:px-8">
            <span className="whitespace-nowrap text-sm font-medium text-ink-700">{user?.name}</span>
            <span className="whitespace-nowrap rounded-lg bg-brand-50 px-2.5 py-1 text-xs font-bold text-brand-700">
              {user?.role}
            </span>
            <button
              onClick={logout}
              className="rounded-lg px-3 py-2 text-sm font-medium text-ink-600 transition-colors hover:bg-ink-100 hover:text-ink-900"
            >
              خروج
            </button>
          </div>
        </header>

        <main className="px-5 py-7 sm:px-8">
          <Outlet />
        </main>
      </div>
    </div>
  );
}

export function PageHeader({ title, subtitle, children }) {
  return (
    <div className="mb-6 flex flex-wrap items-end justify-between gap-4">
      <div>
        <h1 className="text-xl font-black tracking-tight text-ink-900">{title}</h1>
        {subtitle && <p className="mt-1.5 text-sm text-ink-500">{subtitle}</p>}
      </div>
      {children}
    </div>
  );
}
