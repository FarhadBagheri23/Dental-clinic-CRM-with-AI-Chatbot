const fa = new Intl.NumberFormat("fa-IR");
const faDecimal = new Intl.NumberFormat("fa-IR", { maximumFractionDigits: 1 });
const faPrecise = new Intl.NumberFormat("fa-IR", { maximumFractionDigits: 2 });

/** Persian digits with thousands separators. */
export const num = (n) => fa.format(Math.round(Number(n) || 0));

/** A rate, rounded — except that a non-zero rate never renders as ۰٪.
 *
 *  A 0.37% discount is genuinely small, but printing it as "۰٪" next to the
 *  24 million tomans it represents reads as a broken number, not a small one.
 */
export function percent(n) {
  const v = Number(n) || 0;
  const text = v !== 0 && Math.abs(v) < 1 ? faPrecise.format(v) : num(v);
  return `${text}٪`;
}

const SCALES = [
  [1e9, "میلیارد"],
  [1e6, "میلیون"],
  [1e3, "هزار"],
];

/** Compact currency — "۶٫۵ میلیارد تومان". Full figures run to 13 digits,
 *  which no one reads at a glance and which break card layouts. */
export function tomanShort(value) {
  const n = Number(value) || 0;
  for (const [size, label] of SCALES) {
    if (Math.abs(n) >= size) return `${faDecimal.format(n / size)} ${label} تومان`;
  }
  return `${num(n)} تومان`;
}

export const toman = (value) => `${num(value)} تومان`;

// Node and modern browsers ship full ICU, so fa-IR yields Jalali dates with
// no date-library dependency.
export function date(value) {
  if (!value) return "—";
  return new Date(value).toLocaleDateString("fa-IR", {
    year: "numeric",
    month: "2-digit",
    day: "2-digit",
  });
}

export function dateTime(value) {
  if (!value) return "—";
  const d = new Date(value);
  return `${date(value)} — ${d.toLocaleTimeString("fa-IR", {
    hour: "2-digit",
    minute: "2-digit",
  })}`;
}

/** "2026-07" -> "تیر ۰۵" */
export function monthLabel(ym) {
  const [y, m] = String(ym).split("-").map(Number);
  return new Date(y, m - 1, 1).toLocaleDateString("fa-IR", {
    month: "short",
    year: "2-digit",
  });
}
