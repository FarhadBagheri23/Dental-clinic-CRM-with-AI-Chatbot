import { useId } from "react";

import { monthLabel, tomanShort } from "@/shared/lib/format";

const W = 720;
const H = 240;
const PAD = { top: 16, right: 16, bottom: 30, left: 16 };

function line(points) {
  return points.map((p, i) => `${i ? "L" : "M"}${p.x},${p.y}`).join(" ");
}

/**
 * Two-series area chart. Series are drawn right-to-left so the newest month
 * sits where a Persian reader's eye lands last, matching the page direction.
 */
export function AreaChart({ data, series }) {
  const gradientId = useId();

  if (!data?.length) return null;

  const max = Math.max(...data.flatMap((d) => series.map((s) => d[s.key]))) || 1;
  const innerW = W - PAD.left - PAD.right;
  const innerH = H - PAD.top - PAD.bottom;
  const step = data.length > 1 ? innerW / (data.length - 1) : 0;

  // Reversed x: index 0 (oldest) on the right.
  const xAt = (i) => PAD.left + innerW - i * step;
  const yAt = (v) => PAD.top + innerH - (v / max) * innerH;

  return (
    <figure className="m-0">
      <svg
        viewBox={`0 0 ${W} ${H}`}
        className="w-full"
        role="img"
        aria-label={`نمودار ${series.map((s) => s.label).join(" و ")} به تفکیک ماه`}
        preserveAspectRatio="none"
      >
        <defs>
          {series.map((s, i) => (
            <linearGradient key={s.key} id={`${gradientId}-${i}`} x1="0" y1="0" x2="0" y2="1">
              <stop offset="0%" stopColor={s.color} stopOpacity="0.28" />
              <stop offset="100%" stopColor={s.color} stopOpacity="0" />
            </linearGradient>
          ))}
        </defs>

        {/* Gridlines at quarters — enough to read a value, few enough to stay quiet. */}
        {[0, 0.25, 0.5, 0.75, 1].map((t) => (
          <line
            key={t}
            x1={PAD.left}
            x2={W - PAD.right}
            y1={PAD.top + innerH * t}
            y2={PAD.top + innerH * t}
            stroke="currentColor"
            className="text-ink-200"
            strokeWidth="1"
            strokeDasharray={t === 1 ? "0" : "3 5"}
          />
        ))}

        {series.map((s, i) => {
          const pts = data.map((d, idx) => ({ x: xAt(idx), y: yAt(d[s.key]) }));
          const area = `${line(pts)} L${xAt(0)},${PAD.top + innerH} L${xAt(data.length - 1)},${
            PAD.top + innerH
          } Z`;
          return (
            <g key={s.key}>
              <path d={area} fill={`url(#${gradientId}-${i})`} />
              <path
                d={line(pts)}
                fill="none"
                stroke={s.color}
                strokeWidth="2.5"
                strokeLinecap="round"
                strokeLinejoin="round"
              />
              {pts.map((p, idx) => (
                <circle key={idx} cx={p.x} cy={p.y} r="3.5" fill="white" stroke={s.color} strokeWidth="2.5">
                  <title>{`${monthLabel(data[idx].month)} — ${s.label}: ${tomanShort(
                    data[idx][s.key],
                  )}`}</title>
                </circle>
              ))}
            </g>
          );
        })}

        {data.map((d, idx) => (
          <text
            key={d.month}
            x={xAt(idx)}
            y={H - 8}
            textAnchor="middle"
            className="fill-ink-500 text-[11px]"
          >
            {monthLabel(d.month)}
          </text>
        ))}
      </svg>

      <figcaption className="mt-3 flex flex-wrap items-center justify-center gap-5">
        {series.map((s) => (
          <span key={s.key} className="flex items-center gap-2 text-xs text-ink-600">
            <span className="h-2.5 w-2.5 rounded-full" style={{ background: s.color }} />
            {s.label}
          </span>
        ))}
      </figcaption>
    </figure>
  );
}
