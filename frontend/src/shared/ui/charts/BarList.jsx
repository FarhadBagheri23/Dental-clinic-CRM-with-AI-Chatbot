/**
 * Ranked horizontal bars. The bar is a background layer behind the label so
 * the text stays readable at every value — a separate bar column would force
 * the labels into a narrow gutter.
 */
export function BarList({ items }) {
  const max = Math.max(...items.map((i) => i.value)) || 1;

  return (
    <ul className="space-y-1">
      {items.map((item) => (
        <li key={item.label} className="relative overflow-hidden rounded-lg">
          <div
            aria-hidden="true"
            className="absolute inset-y-0 right-0 bg-brand-100/70 transition-[width] duration-500"
            style={{ width: `${Math.max((item.value / max) * 100, 2)}%` }}
          />
          <div className="relative flex items-center justify-between gap-4 px-3 py-2.5">
            <span className="min-w-0 truncate text-sm font-medium text-ink-800">
              {item.label}
              {item.sub && <span className="mr-2 text-xs font-normal text-ink-500">{item.sub}</span>}
            </span>
            <span className="shrink-0 text-sm font-bold tabular-nums text-ink-900">
              {item.display}
            </span>
          </div>
        </li>
      ))}
    </ul>
  );
}
