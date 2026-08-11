import { createContext, useCallback, useContext, useMemo, useState } from "react";

import { analyticsApi } from "@/features/analytics/api/analyticsApi";
import { useApiQuery } from "@/shared/hooks/useApiQuery";

const EMPTY = { date_from: "", date_to: "", specialty: "", category: "", insurance: "" };

/** Persian names for the filter keys, so a chart can say which one it had to
 *  ignore without every caller re-deriving the wording. */
export const FILTER_LABELS = {
  date_from: "از تاریخ",
  date_to: "تا تاریخ",
  specialty: "تخصص پزشک",
  category: "دسته خدمت",
  insurance: "شرکت بیمه",
};

const FiltersContext = createContext(null);

/** Global dashboard filters (report §۷), shared across every analytics page
 *  so switching pages keeps the current selection.
 *
 *  The filter *options* are fetched here rather than in FilterBar because
 *  they also carry the `unsupported` map, and every card wanting to declare
 *  an ignored filter would otherwise refetch the same document — useApiQuery
 *  has no cache.
 */
export function FiltersProvider({ children }) {
  const [filters, setFilters] = useState(EMPTY);
  const { data: options } = useApiQuery((s) => analyticsApi.options(s));

  const set = useCallback((key, value) => {
    setFilters((f) => ({ ...f, [key]: value }));
  }, []);

  const reset = useCallback(() => setFilters(EMPTY), []);

  // A stable query string is the dependency every page keys its fetch on;
  // passing the object itself would refetch on every render.
  const queryString = useMemo(() => {
    const params = new URLSearchParams();
    for (const [k, v] of Object.entries(filters)) if (v) params.set(k, v);
    const s = params.toString();
    return s ? `?${s}` : "";
  }, [filters]);

  const activeCount = useMemo(
    () => Object.values(filters).filter(Boolean).length,
    [filters],
  );

  /** Filters the user has set that the given endpoint cannot honour.
   *
   *  The server owns this list, because some pipelines genuinely cannot apply
   *  some filters — a cancelled appointment produced no session, so it has no
   *  service category to match. Reading it from the API instead of hardcoding
   *  it here keeps the note the UI shows from drifting away from what the
   *  pipeline actually did.
   */
  const ignoredFor = useCallback(
    (endpoint) =>
      (options?.unsupported?.[endpoint] ?? []).filter((key) => filters[key]),
    [options, filters],
  );

  const value = useMemo(
    () => ({ filters, set, reset, queryString, activeCount, options, ignoredFor }),
    [filters, set, reset, queryString, activeCount, options, ignoredFor],
  );

  return <FiltersContext.Provider value={value}>{children}</FiltersContext.Provider>;
}

export function useFilters() {
  const ctx = useContext(FiltersContext);
  if (!ctx) throw new Error("useFilters must be used inside <FiltersProvider>");
  return ctx;
}
