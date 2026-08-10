import { ToothMark } from "@/shared/ui/Logo";

/** Shown while the session check is in flight. */
export function SplashScreen() {
  return (
    <div className="grid min-h-dvh place-items-center bg-ink-100">
      <div className="flex flex-col items-center gap-4 text-brand-700">
        <ToothMark className="h-10 w-10 animate-pulse" />
        <span className="sr-only">در حال بررسی نشست کاربر…</span>
      </div>
    </div>
  );
}
