/**
 * A short interpretation printed under a chart. Report §۷ asks each page to
 * state its insight, and a number without its reading is not intelligence.
 */
export function Insight({ children, tone = "info" }) {
  const tones = {
    info: "border-brand-200 bg-brand-50/60 text-brand-900",
    warn: "border-accent-200 bg-accent-50/70 text-accent-700",
    caution: "border-rose-200 bg-rose-50/70 text-rose-800",
  };
  return (
    <p className={`mt-4 rounded-xl border px-4 py-3 text-[13px] leading-7 ${tones[tone]}`}>
      <span className="font-black">بینش: </span>
      {children}
    </p>
  );
}
