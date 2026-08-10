import { Navigate } from "react-router-dom";

import { LoginForm } from "@/features/auth/components/LoginForm";
import { useAuth } from "@/features/auth/hooks/useAuth";
import { LogoLockup } from "@/shared/ui/Logo";
import { SplashScreen } from "@/shared/ui/SplashScreen";

const HIGHLIGHTS = [
  "گزارش درآمد، وصولی و مطالبات معوق",
  "پرونده بیماران، نوبت‌ها و فاکتورها",
  "پایش موجودی اقلام مصرفی",
];

export function LoginPage() {
  const { status } = useAuth();

  if (status === "loading") return <SplashScreen />;
  if (status === "authenticated") return <Navigate to="/dashboard" replace />;

  return (
    <main className="grid min-h-dvh lg:grid-cols-[1.05fr_1fr]">
      {/* Form panel. First in the DOM so keyboard and screen-reader users
          reach the inputs without traversing decorative content. */}
      <div className="flex items-center justify-center px-6 py-12 sm:px-10">
        <div className="w-full max-w-[26rem] animate-fade-up">
          <LogoLockup className="mb-10" />

          <h1 className="text-2xl font-black tracking-tight text-ink-900">
            ورود به پنل مدیریت
          </h1>
          <p className="mb-8 mt-2 text-sm leading-7 text-ink-500">
            این بخش مخصوص کادر درمان و مدیریت کلینیک است.
          </p>

          <LoginForm />
        </div>
      </div>

      {/* Brand panel — decorative, hidden on small screens. */}
      <aside
        aria-hidden="true"
        className="relative hidden overflow-hidden bg-brand-900 lg:block"
      >
        <div className="absolute inset-0 bg-[radial-gradient(120%_90%_at_15%_0%,#1f757b_0%,#1a3f45_45%,#0a252a_100%)]" />

        {/* Concentric arcs — a quiet nod to a dental scan, not a stock blob. */}
        <svg
          className="absolute -left-24 top-1/2 h-[46rem] w-[46rem] -translate-y-1/2 text-white/[0.07]"
          viewBox="0 0 400 400"
          fill="none"
          stroke="currentColor"
        >
          {[70, 110, 150, 190].map((r) => (
            <circle key={r} cx="200" cy="200" r={r} strokeWidth="1.5" />
          ))}
          <circle cx="200" cy="200" r="30" fill="currentColor" stroke="none" />
        </svg>

        <div className="relative flex h-full flex-col justify-between p-14">
          <LogoLockup tone="light" />

          <div className="max-w-md">
            <p className="text-[2rem] font-black leading-[1.6] text-white">
              همه‌ی داده‌های کلینیک،
              <br />
              <span className="text-accent-300">در یک نگاه.</span>
            </p>
            <ul className="mt-8 space-y-3.5">
              {HIGHLIGHTS.map((item) => (
                <li key={item} className="flex items-center gap-3 text-sm text-brand-100/85">
                  <span className="h-1.5 w-1.5 shrink-0 rounded-full bg-accent-400" />
                  {item}
                </li>
              ))}
            </ul>
          </div>

          <p className="text-xs text-brand-200/50">
            سامانه هوش تجاری کلینیک — دانشگاه صنعتی شریف
          </p>
        </div>
      </aside>
    </main>
  );
}
