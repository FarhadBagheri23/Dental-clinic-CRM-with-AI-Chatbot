// Keyed by the Persian status values that live in the data.
const TONES = {
  "انجام‌شده": "bg-emerald-50 text-emerald-700 border-emerald-200",
  "پرداخت‌شده": "bg-emerald-50 text-emerald-700 border-emerald-200",
  رزرو: "bg-brand-50 text-brand-700 border-brand-200",
  بخشی: "bg-accent-50 text-accent-700 border-accent-200",
  لغو: "bg-ink-100 text-ink-600 border-ink-200",
  غایب: "bg-rose-50 text-rose-700 border-rose-200",
  معوق: "bg-rose-50 text-rose-700 border-rose-200",
};

export function Badge({ children }) {
  const tone = TONES[children] ?? "bg-ink-100 text-ink-600 border-ink-200";
  return (
    <span
      className={`inline-block whitespace-nowrap rounded-full border px-2.5 py-0.5 text-[11px] font-bold ${tone}`}
    >
      {children}
    </span>
  );
}
