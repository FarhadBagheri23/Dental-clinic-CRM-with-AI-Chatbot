import { percent, tomanShort } from "@/shared/lib/format";

/**
 * Single horizontal stacked bar — used for the receivables waterfall, where
 * the parts sum to a meaningful whole and their relative size is the point.
 */
export function StackedBar({ segments, total, format = tomanShort }) {
  const sum = total || segments.reduce((s, x) => s + x.value, 0) || 1;

  return (
    <div>
      <div className="flex h-11 w-full overflow-hidden rounded-xl" role="img"
        aria-label={segments.map((s) => `${s.label}: ${format(s.value)}`).join("، ")}>
        {segments.map((s) => {
          const pct = (s.value / sum) * 100;
          if (pct <= 0) return null;
          return (
            <div key={s.label} style={{ width: `${pct}%`, background: s.color }}
              className="grid place-items-center transition-[width] duration-500">
              <title>{`${s.label}: ${format(s.value)}`}</title>
              {pct > 12 && (
                <span className="px-2 text-[11px] font-bold text-white tabular-nums">
                  {percent(Math.round(pct))}
                </span>
              )}
            </div>
          );
        })}
      </div>

      <ul className="mt-4 grid gap-2.5 sm:grid-cols-2">
        {segments.map((s) => (
          <li key={s.label} className="flex items-center justify-between gap-3 text-sm">
            <span className="flex items-center gap-2.5 text-ink-600">
              <span className="h-2.5 w-2.5 shrink-0 rounded-full" style={{ background: s.color }} />
              {s.label}
            </span>
            <span className="font-bold tabular-nums text-ink-800">{format(s.value)}</span>
          </li>
        ))}
      </ul>
    </div>
  );
}
