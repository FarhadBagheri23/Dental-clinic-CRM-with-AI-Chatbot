import { num } from "@/shared/lib/format";

/** Grey blocks matching the shape of the content being loaded, so the layout
 *  does not jump when data arrives. */
export function Skeleton({ className = "h-4 w-full" }) {
  return <div className={`animate-pulse rounded-lg bg-ink-200/70 ${className}`} />;
}

export function CardSkeleton({ rows = 4 }) {
  return (
    <div className="space-y-3">
      {Array.from({ length: rows }, (_, i) => (
        <Skeleton key={i} className={`h-9 ${i % 3 === 2 ? "w-4/5" : "w-full"}`} />
      ))}
    </div>
  );
}

export function ErrorState({ message, className = "" }) {
  return (
    <div
      role="alert"
      className={`rounded-xl border border-rose-200 bg-rose-50 px-4 py-6 text-center text-sm text-rose-800 ${className}`}
    >
      {message || "خطا در دریافت اطلاعات."}
    </div>
  );
}

export function EmptyState({ title, hint }) {
  return (
    <div className="px-4 py-16 text-center">
      <p className="text-sm font-bold text-ink-700">{title}</p>
      {hint && <p className="mt-1.5 text-xs text-ink-400">{hint}</p>}
    </div>
  );
}

/** Renders the loading / error / empty / loaded states of one `useApiQuery`.
 *
 *  Was copy-pasted into five pages in three subtly different variants: one
 *  tested `!data`, one `!data?.length`, and one handled both. The third is
 *  the only correct one for every caller — the array test alone treated a
 *  populated object payload as empty — so it is the one kept here.
 *
 *  `children` is a function so the data is unwrapped only once it is known
 *  to exist, which is what lets callers drop their `?.` chains.
 */
export function Panel({ query, children, rows = 5 }) {
  if (query.loading) return <CardSkeleton rows={rows} />;
  if (query.error) return <ErrorState message={query.error} />;

  const empty = Array.isArray(query.data) ? !query.data.length : !query.data;
  if (empty) return <EmptyState title="داده‌ای در این بازه نیست." hint="فیلترها را تغییر دهید." />;

  return children(query.data);
}

export function Pagination({ meta, onChange }) {
  if (!meta || meta.pages <= 1) return null;

  const button =
    "rounded-lg border border-ink-300 px-4 py-2 text-sm font-medium text-ink-700 transition-colors hover:bg-ink-50 disabled:cursor-not-allowed disabled:opacity-40";

  return (
    <div className="flex flex-wrap items-center justify-between gap-3 border-t border-ink-100 px-5 py-4">
      <span className="text-xs text-ink-500">
        صفحه {num(meta.page)} از {num(meta.pages)} — مجموع {num(meta.total)} رکورد
      </span>
      <div className="flex gap-2">
        <button className={button} disabled={meta.page <= 1} onClick={() => onChange(meta.page - 1)}>
          قبلی
        </button>
        <button
          className={button}
          disabled={meta.page >= meta.pages}
          onClick={() => onChange(meta.page + 1)}
        >
          بعدی
        </button>
      </div>
    </div>
  );
}

export function FilterTabs({ options, value, onChange }) {
  return (
    <div className="flex flex-wrap gap-2" role="group" aria-label="فیلتر وضعیت">
      {options.map((o) => {
        const active = (value ?? "") === o.value;
        return (
          <button
            key={o.label}
            onClick={() => onChange(o.value)}
            aria-pressed={active}
            className={`rounded-lg px-4 py-2 text-sm font-medium transition-colors ${
              active
                ? "bg-brand-700 text-white shadow-card"
                : "border border-ink-300 text-ink-600 hover:bg-ink-50"
            }`}
          >
            {o.label}
          </button>
        );
      })}
    </div>
  );
}
