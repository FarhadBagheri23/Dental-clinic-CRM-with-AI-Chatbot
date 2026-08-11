import { FILTER_LABELS, useFilters } from "@/app/providers/FiltersProvider";

/** Declares a filter the chart above could not apply.
 *
 *  Six endpoints genuinely cannot honour some filters — a cancelled
 *  appointment produced no session, so it has no service category, and
 *  filtering by one would silently delete every cancellation from a
 *  cancellation chart. Rather than approximate, those pipelines ignore the
 *  filter and say so here.
 *
 *  Renders nothing when the user has not set an affected filter, so it can be
 *  dropped into any card unconditionally.
 */
export function FilterNote({ endpoint }) {
  const { ignoredFor } = useFilters();
  const ignored = ignoredFor(endpoint);

  if (!ignored.length) return null;

  const names = ignored.map((key) => `«${FILTER_LABELS[key]}»`).join(" و ");

  return (
    <p className="mt-3 flex items-start gap-2 rounded-lg bg-amber-50 px-3 py-2 text-xs leading-6 text-amber-900">
      <svg viewBox="0 0 16 16" className="mt-1 h-3.5 w-3.5 shrink-0" fill="currentColor" aria-hidden="true">
        <path d="M8 1.5 15 14H1L8 1.5Zm0 4.2a.7.7 0 0 0-.7.7v3a.7.7 0 0 0 1.4 0v-3a.7.7 0 0 0-.7-.7Zm0 5.6a.85.85 0 1 0 0 1.7.85.85 0 0 0 0-1.7Z" />
      </svg>
      <span>
        فیلتر {names} روی این نمودار اعمال نشده است — این داده به خدمت مشخصی
        وصل نیست، پس اعمال آن عدد را دقیق‌تر نمی‌کرد، فقط بخشی از رکوردها را
        بی‌صدا حذف می‌کرد.
      </span>
    </p>
  );
}
