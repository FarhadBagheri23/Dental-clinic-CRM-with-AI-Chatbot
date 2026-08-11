import { useFilters } from "@/app/providers/FiltersProvider";
import { JalaliDateInput } from "@/shared/ui/JalaliDateInput";

function Select({ label, value, onChange, options, placeholder }) {
  return (
    <label className="flex min-w-0 flex-col gap-1.5">
      <span className="text-[11px] font-bold text-ink-500">{label}</span>
      <select
        value={value}
        onChange={(e) => onChange(e.target.value)}
        className="h-10 min-w-0 rounded-lg border border-ink-200 bg-white px-3 text-sm
          text-ink-800 transition-colors hover:border-ink-300
          focus:border-brand-500 focus:outline-none focus:ring-2 focus:ring-brand-200"
      >
        <option value="">{placeholder}</option>
        {options.map((o) => (
          <option key={o} value={o}>{o}</option>
        ))}
      </select>
    </label>
  );
}

/** Global filter bar — report §۷ "فیلترهای سراسری". */
export function FilterBar() {
  // Options come from the provider, which fetches them once for the whole
  // app — this used to be a second request for the same document.
  const { filters, set, reset, activeCount, options: data } = useFilters();

  const bounds = {
    min: data?.date_min?.slice(0, 10),
    max: data?.date_max?.slice(0, 10),
  };

  return (
    <section
      aria-label="فیلترهای سراسری"
      className="mb-6 rounded-2xl border border-ink-200/80 bg-white p-4 shadow-card"
    >
      <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-5">
        <JalaliDateInput label="از تاریخ" value={filters.date_from} onChange={(v) => set("date_from", v)} {...bounds} />
        <JalaliDateInput label="تا تاریخ" value={filters.date_to} onChange={(v) => set("date_to", v)} {...bounds} />
        <Select
          label="تخصص پزشک"
          value={filters.specialty}
          onChange={(v) => set("specialty", v)}
          options={data?.specialties ?? []}
          placeholder="همه تخصص‌ها"
        />
        <Select
          label="دسته خدمت"
          value={filters.category}
          onChange={(v) => set("category", v)}
          options={data?.categories ?? []}
          placeholder="همه دسته‌ها"
        />
        <Select
          label="شرکت بیمه"
          value={filters.insurance}
          onChange={(v) => set("insurance", v)}
          options={data?.insurers ?? []}
          placeholder="همه بیمه‌ها"
        />
      </div>

      {activeCount > 0 && (
        <div className="mt-3 flex items-center justify-between gap-4 border-t border-ink-100 pt-3">
          {/* Deliberately no longer claims every chart honoured every filter:
              a few genuinely cannot, and each of those says so on its own
              card. A blanket promise here was the misleading part. */}
          <span className="text-xs text-ink-500">
            {`${activeCount} فیلتر فعال — نمودارهایی که فیلتری را اعمال نکرده‌اند، زیر همان نمودار توضیح داده‌اند.`}
          </span>
          <button
            onClick={reset}
            className="rounded-lg border border-ink-300 px-3 py-1.5 text-xs font-bold text-ink-700 transition-colors hover:bg-ink-50"
          >
            حذف فیلترها
          </button>
        </div>
      )}
    </section>
  );
}
