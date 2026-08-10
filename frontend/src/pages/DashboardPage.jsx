import { useAuth } from "@/features/auth/hooks/useAuth";
import { Button } from "@/shared/ui/Button";
import { LogoLockup } from "@/shared/ui/Logo";

/** Placeholder so the post-login redirect lands somewhere real. Replaced
 *  when the dashboard endpoints land. */
export function DashboardPage() {
  const { user, logout } = useAuth();

  return (
    <div className="min-h-dvh">
      <header className="border-b border-ink-200 bg-white">
        <div className="mx-auto flex max-w-6xl items-center justify-between gap-4 px-6 py-4">
          <LogoLockup />
          <div className="flex items-center gap-3">
            <span className="whitespace-nowrap text-sm font-medium text-ink-700">
              {user?.name}
            </span>
            <span className="whitespace-nowrap rounded-lg bg-brand-50 px-2.5 py-1 text-xs font-bold text-brand-700">
              {user?.role}
            </span>
            <Button variant="ghost" className="w-auto" onClick={logout}>
              خروج
            </Button>
          </div>
        </div>
      </header>

      <main className="mx-auto max-w-6xl px-6 py-12">
        <div className="rounded-2xl border border-dashed border-ink-300 bg-white p-12 text-center">
          <h1 className="text-lg font-black text-ink-900">داشبورد مدیریتی</h1>
          <p className="mt-2 text-sm text-ink-500">
            نقاط پایانی داشبورد در گام بعدی اضافه می‌شوند.
          </p>
        </div>
      </main>
    </div>
  );
}
