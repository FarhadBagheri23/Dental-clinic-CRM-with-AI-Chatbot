import { num, percent } from "@/shared/lib/format";

const SIZE = 168;
const STROKE = 22;
const R = (SIZE - STROKE) / 2;
const C = 2 * Math.PI * R;

/** Ring chart with the total in the middle and a legend beside it. */
export function Donut({ data, colors, centerLabel, centerValue }) {
  const total = data.reduce((sum, d) => sum + d.n, 0);
  if (!total) return null;

  let offset = 0;

  return (
    <div className="flex flex-wrap items-center justify-center gap-8">
      <div className="relative shrink-0" style={{ width: SIZE, height: SIZE }}>
        <svg
          viewBox={`0 0 ${SIZE} ${SIZE}`}
          className="-rotate-90"
          width={SIZE}
          height={SIZE}
          role="img"
          aria-label={data.map((d) => `${d.status}: ${d.n}`).join("، ")}
        >
          <circle cx={SIZE / 2} cy={SIZE / 2} r={R} fill="none" strokeWidth={STROKE} className="stroke-ink-100" />
          {data.map((d, i) => {
            const length = (d.n / total) * C;
            const el = (
              <circle
                key={d.status}
                cx={SIZE / 2}
                cy={SIZE / 2}
                r={R}
                fill="none"
                strokeWidth={STROKE}
                stroke={colors[i % colors.length]}
                strokeDasharray={`${length} ${C - length}`}
                strokeDashoffset={-offset}
                strokeLinecap="butt"
              >
                <title>{`${d.status}: ${num(d.n)} (${percent(Math.round((d.n / total) * 100))})`}</title>
              </circle>
            );
            offset += length;
            return el;
          })}
        </svg>

        <div className="absolute inset-0 grid place-content-center text-center">
          <span className="text-xl font-black text-ink-900">{centerValue ?? num(total)}</span>
          <span className="mt-0.5 text-[11px] text-ink-500">{centerLabel}</span>
        </div>
      </div>

      <ul className="min-w-[9rem] space-y-2.5">
        {data.map((d, i) => (
          <li key={d.status} className="flex items-center justify-between gap-4 text-sm">
            <span className="flex items-center gap-2.5 text-ink-600">
              <span
                className="h-2.5 w-2.5 shrink-0 rounded-full"
                style={{ background: colors[i % colors.length] }}
              />
              {d.status}
            </span>
            <span className="font-bold tabular-nums text-ink-800">{num(d.n)}</span>
          </li>
        ))}
      </ul>
    </div>
  );
}
