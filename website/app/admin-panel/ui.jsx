// Shared presentation helpers for the CRM. Server-safe (no client hooks).

export const fa = (n) => Number(n ?? 0).toLocaleString("fa-IR");
export const toman = (n) => `${fa(Math.round(n ?? 0))} تومان`;

// Node 20 ships full ICU, so fa-IR formatting yields Jalali dates with no
// extra dependency.
export const faDate = (d) =>
  d ? new Date(d).toLocaleDateString("fa-IR", { year: "numeric", month: "2-digit", day: "2-digit" }) : "—";

export const faDateTime = (d) =>
  d
    ? `${faDate(d)} — ${new Date(d).toLocaleTimeString("fa-IR", {
        hour: "2-digit",
        minute: "2-digit",
      })}`
    : "—";

const TONES = {
  "انجام‌شده": "bg-emerald-50 text-emerald-700 border-emerald-200",
  "پرداخت‌شده": "bg-emerald-50 text-emerald-700 border-emerald-200",
  رزرو: "bg-sky-50 text-sky-700 border-sky-200",
  بخشی: "bg-amber-50 text-amber-700 border-amber-200",
  لغو: "bg-slate-100 text-slate-600 border-slate-200",
  غایب: "bg-rose-50 text-rose-700 border-rose-200",
  معوق: "bg-rose-50 text-rose-700 border-rose-200",
};

export function Badge({ children }) {
  const tone = TONES[children] ?? "bg-slate-100 text-slate-600 border-slate-200";
  return (
    <span className={`inline-block whitespace-nowrap rounded-full border px-2.5 py-0.5 text-[11px] font-bold ${tone}`}>
      {children}
    </span>
  );
}

export function PageHead({ title, sub, children }) {
  return (
    <div className="mb-7 flex flex-wrap items-end justify-between gap-4">
      <div>
        <h1 className="text-2xl font-black text-slate-900">{title}</h1>
        {sub ? <p className="mt-1.5 text-sm text-slate-500">{sub}</p> : null}
      </div>
      {children}
    </div>
  );
}

export function Card({ label, value, hint, tone = "text-slate-900" }) {
  return (
    <div className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">
      <div className="text-xs text-slate-500">{label}</div>
      <div className={`mt-1.5 text-2xl font-black ${tone}`}>{value}</div>
      {hint ? <div className="mt-1 text-xs text-slate-400">{hint}</div> : null}
    </div>
  );
}

export function Table({ head, children, empty = "رکوردی یافت نشد." }) {
  const rows = Array.isArray(children) ? children : [children];
  const isEmpty = rows.flat().filter(Boolean).length === 0;

  return (
    <div className="overflow-hidden rounded-2xl border border-slate-200 bg-white shadow-sm">
      <div className="overflow-x-auto">
        <table className="w-full text-right text-sm">
          <thead className="border-b border-slate-200 bg-slate-50 text-xs text-slate-500">
            <tr>
              {head.map((h) => (
                <th key={h} className="whitespace-nowrap px-4 py-3 font-bold">
                  {h}
                </th>
              ))}
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-100">
            {isEmpty ? (
              <tr>
                <td colSpan={head.length} className="px-4 py-14 text-center text-slate-400">
                  {empty}
                </td>
              </tr>
            ) : (
              children
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}

export function Pagination({ meta, basePath, params = {} }) {
  if (meta.pages <= 1) return null;
  const link = (p) => {
    const q = new URLSearchParams({ ...params, page: String(p) });
    return `${basePath}?${q}`;
  };

  return (
    <div className="mt-5 flex items-center justify-between text-sm">
      <span className="text-slate-500">
        صفحه {fa(meta.page)} از {fa(meta.pages)} — مجموع {fa(meta.total)} رکورد
      </span>
      <div className="flex gap-2">
        {meta.page > 1 ? (
          <a href={link(meta.page - 1)} className="rounded-lg border border-slate-300 px-4 py-2 font-medium transition hover:bg-slate-50">
            قبلی
          </a>
        ) : null}
        {meta.page < meta.pages ? (
          <a href={link(meta.page + 1)} className="rounded-lg border border-slate-300 px-4 py-2 font-medium transition hover:bg-slate-50">
            بعدی
          </a>
        ) : null}
      </div>
    </div>
  );
}

export function FilterTabs({ options, active, basePath, param = "status" }) {
  return (
    <div className="mb-5 flex flex-wrap gap-2">
      {options.map((o) => {
        const on = (active ?? "") === o.value;
        const q = o.value ? `${basePath}?${param}=${encodeURIComponent(o.value)}` : basePath;
        return (
          <a
            key={o.label}
            href={q}
            className={`rounded-lg px-4 py-2 text-sm font-medium transition ${
              on ? "bg-brand-600 text-white shadow-sm" : "border border-slate-300 text-slate-600 hover:bg-slate-50"
            }`}
          >
            {o.label}
          </a>
        );
      })}
    </div>
  );
}
