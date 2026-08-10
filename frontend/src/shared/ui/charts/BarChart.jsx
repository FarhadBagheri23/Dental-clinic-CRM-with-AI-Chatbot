import { num } from "@/shared/lib/format";

/**
 * Vertical bars with an optional second series drawn as a line (combo).
 * Categories run right-to-left to match page direction.
 */
export function BarChart({ data, xKey, bars, line, formatValue = num, height = 220 }) {
  if (!data?.length) return null;

  const W = 720;
  const PAD = { top: 14, right: 12, bottom: 34, left: 12 };
  const innerW = W - PAD.left - PAD.right;
  const innerH = height - PAD.top - PAD.bottom;

  const maxBar = Math.max(...data.flatMap((d) => bars.map((b) => d[b.key]))) || 1;
  const maxLine = line ? Math.max(...data.map((d) => d[line.key])) || 1 : 1;

  const slot = innerW / data.length;
  const barW = Math.min(slot * 0.52, 46) / bars.length;
  // Reversed: first item on the right.
  const centre = (i) => PAD.left + innerW - (i + 0.5) * slot;
  const yBar = (v) => PAD.top + innerH - (v / maxBar) * innerH;
  const yLine = (v) => PAD.top + innerH - (v / maxLine) * innerH;

  const linePts = line
    ? data.map((d, i) => `${centre(i)},${yLine(d[line.key])}`).join(" ")
    : null;

  return (
    <figure className="m-0">
      <svg viewBox={`0 0 ${W} ${height}`} className="w-full" role="img"
        aria-label={`نمودار ${bars.map((b) => b.label).join(" و ")}`}>
        {[0.25, 0.5, 0.75, 1].map((t) => (
          <line key={t} x1={PAD.left} x2={W - PAD.right}
            y1={PAD.top + innerH * t} y2={PAD.top + innerH * t}
            stroke="currentColor" className="text-ink-200" strokeWidth="1"
            strokeDasharray={t === 1 ? "0" : "3 5"} />
        ))}

        {data.map((d, i) =>
          bars.map((b, bi) => {
            const h = Math.max(innerH - (yBar(d[b.key]) - PAD.top), 1);
            return (
              <rect key={`${b.key}-${i}`}
                x={centre(i) - (barW * bars.length) / 2 + bi * barW}
                y={yBar(d[b.key])} width={barW - 3} height={h}
                rx="4" fill={b.color}>
                <title>{`${d[xKey]} — ${b.label}: ${formatValue(d[b.key])}`}</title>
              </rect>
            );
          }),
        )}

        {line && (
          <>
            <polyline points={linePts} fill="none" stroke={line.color}
              strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round" />
            {data.map((d, i) => (
              <circle key={i} cx={centre(i)} cy={yLine(d[line.key])} r="3.5"
                fill="white" stroke={line.color} strokeWidth="2.5">
                <title>{`${d[xKey]} — ${line.label}: ${num(d[line.key])}`}</title>
              </circle>
            ))}
          </>
        )}

        {data.map((d, i) => (
          <text key={i} x={centre(i)} y={height - 10} textAnchor="middle"
            className="fill-ink-500 text-[11px]">
            {String(d[xKey]).length > 12 ? `${String(d[xKey]).slice(0, 11)}…` : d[xKey]}
          </text>
        ))}
      </svg>

      <figcaption className="mt-3 flex flex-wrap items-center justify-center gap-5">
        {[...bars, ...(line ? [line] : [])].map((s) => (
          <span key={s.key} className="flex items-center gap-2 text-xs text-ink-600">
            <span className="h-2.5 w-2.5 rounded-full" style={{ background: s.color }} />
            {s.label}
          </span>
        ))}
      </figcaption>
    </figure>
  );
}
