/** Inline trend line for a KPI card.
 *
 *  ponytail: hand-rolled SVG rather than a charting dependency — a sparkline
 *  is a polyline over a normalised array, and the existing charts are built
 *  the same way. Axes, ticks and tooltips are deliberately absent; the point
 *  is the shape, and the number above it carries the magnitude.
 */
export function Sparkline({ values, color = "#1f757b", height = 34 }) {
  const points = values.filter((v) => Number.isFinite(v));
  if (points.length < 2) return null;

  const W = 100;
  const min = Math.min(...points);
  const max = Math.max(...points);
  // A flat series would divide by zero; draw it down the middle instead.
  const span = max - min || 1;
  const step = W / (points.length - 1);

  const xy = points.map((v, i) => [
    i * step,
    height - 2 - ((v - min) / span) * (height - 4),
  ]);
  const line = xy.map(([x, y]) => `${x.toFixed(1)},${y.toFixed(1)}`).join(" ");
  const area = `${line} ${W},${height} 0,${height}`;
  const [lastX, lastY] = xy.at(-1);
  const id = `spark-${color.slice(1)}`;

  return (
    <svg
      viewBox={`0 0 ${W} ${height}`}
      // preserveAspectRatio="none" lets the line stretch to the card width;
      // the marker below is drawn in a separate, unscaled overlay instead.
      preserveAspectRatio="none"
      className="mt-3 w-full"
      style={{ height }}
      aria-hidden="true"
    >
      <defs>
        <linearGradient id={id} x1="0" y1="0" x2="0" y2="1">
          <stop offset="0%" stopColor={color} stopOpacity="0.22" />
          <stop offset="100%" stopColor={color} stopOpacity="0" />
        </linearGradient>
      </defs>
      <polygon points={area} fill={`url(#${id})`} />
      <polyline
        points={line}
        fill="none"
        stroke={color}
        strokeWidth="1.6"
        strokeLinecap="round"
        strokeLinejoin="round"
        vectorEffect="non-scaling-stroke"
      />
      <circle cx={lastX} cy={lastY} r="2" fill={color} vectorEffect="non-scaling-stroke" />
    </svg>
  );
}
