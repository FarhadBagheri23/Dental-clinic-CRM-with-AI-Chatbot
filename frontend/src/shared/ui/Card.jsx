export function Card({ title, action, children, className = "", bodyClassName = "" }) {
  return (
    <section
      className={`rounded-2xl border border-ink-200/80 bg-white shadow-card ${className}`}
    >
      {(title || action) && (
        <header className="flex items-center justify-between gap-4 border-b border-ink-100 px-5 py-4">
          <h2 className="text-sm font-black text-ink-900">{title}</h2>
          {action}
        </header>
      )}
      <div className={bodyClassName || "p-5"}>{children}</div>
    </section>
  );
}

const TONES = {
  default: "text-ink-900",
  positive: "text-emerald-700",
  negative: "text-rose-700",
  info: "text-brand-700",
};

export function StatCard({ label, value, hint, tone = "default", icon }) {
  return (
    <div className="rounded-2xl border border-ink-200/80 bg-white p-5 shadow-card transition-shadow hover:shadow-lift">
      <div className="flex items-start justify-between gap-3">
        <span className="text-xs font-medium text-ink-500">{label}</span>
        {icon && (
          <span className="grid h-8 w-8 shrink-0 place-items-center rounded-xl bg-brand-50 text-brand-700">
            {icon}
          </span>
        )}
      </div>
      {/* tabular-nums keeps digits from shifting width between renders. */}
      <div className={`mt-2 text-[1.35rem] font-black tabular-nums leading-tight ${TONES[tone]}`}>
        {value}
      </div>
      {hint && <div className="mt-1.5 text-xs text-ink-400">{hint}</div>}
    </div>
  );
}
