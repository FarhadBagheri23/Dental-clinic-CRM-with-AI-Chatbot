import { percent } from "@/shared/lib/format";
import { Sparkline } from "@/shared/ui/charts/Sparkline";

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

// Sparkline stroke per tone — hex rather than a Tailwind class because the
// SVG takes it as an attribute, not a className.
const SPARK_TONES = {
  default: "#5f6a6b",
  positive: "#047857",
  negative: "#e11d48",
  info: "#1f757b",
};

/** Period-over-period change chip.
 *
 *  `invert` marks a metric where falling is the good outcome — lost
 *  appointments, outstanding receivables. Without it a card would paint a
 *  drop in no-shows red, which is exactly backwards.
 */
function Delta({ value, invert = false }) {
  if (!Number.isFinite(value)) return null;
  const flat = Math.abs(value) < 0.05;
  const good = invert ? value < 0 : value > 0;
  const cls = flat
    ? "bg-ink-100 text-ink-500"
    : good
      ? "bg-emerald-50 text-emerald-700"
      : "bg-rose-50 text-rose-700";

  const direction = value > 0 ? "افزایش" : "کاهش";
  const text = percent(Math.abs(Math.round(value * 10) / 10));

  return (
    <span
      // The chip is a bare number next to a much larger one; without this the
      // reader has to guess what it is a percentage *of*.
      title={flat ? "بدون تغییر نسبت به ماه قبل" : `${direction} ${text} نسبت به ماه قبل`}
      aria-label={flat ? "بدون تغییر نسبت به ماه قبل" : `${direction} ${text} نسبت به ماه قبل`}
      className={`inline-flex items-center gap-1 rounded-lg px-1.5 py-0.5 text-[11px] font-bold tabular-nums ${cls}`}
    >
      {!flat && (
        <svg viewBox="0 0 12 12" className="h-2.5 w-2.5" fill="currentColor" aria-hidden="true">
          <path d={value > 0 ? "M6 2l4 6H2z" : "M6 10L2 4h8z"} />
        </svg>
      )}
      {text}
    </span>
  );
}

export function StatCard({
  label, value, hint, tone = "default", icon,
  delta, invertDelta = false, spark, sparkColor,
}) {
  return (
    <div className="flex flex-col rounded-2xl border border-ink-200/80 bg-white p-5 shadow-card transition-shadow hover:shadow-lift">
      <div className="flex items-start justify-between gap-3">
        <span className="text-xs font-medium text-ink-500">{label}</span>
        {icon && (
          <span className="grid h-8 w-8 shrink-0 place-items-center rounded-xl bg-brand-50 text-brand-700">
            {icon}
          </span>
        )}
      </div>
      {/* tabular-nums keeps digits from shifting width between renders. */}
      <div className="mt-2 flex flex-wrap items-baseline gap-2">
        <span className={`text-[1.35rem] font-black tabular-nums leading-tight ${TONES[tone]}`}>
          {value}
        </span>
        <Delta value={delta} invert={invertDelta} />
      </div>
      {hint && <div className="mt-1.5 text-xs text-ink-400">{hint}</div>}
      {spark?.length > 1 && (
        // mt-auto pins the trend line to the bottom so cards of differing
        // hint lengths still line their sparklines up across the row.
        <div className="mt-auto">
          <Sparkline values={spark} color={sparkColor ?? SPARK_TONES[tone]} />
        </div>
      )}
    </div>
  );
}
