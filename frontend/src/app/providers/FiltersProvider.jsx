import { createContext, useCallback, useContext, useMemo, useState } from "react";

const EMPTY = { date_from: "", date_to: "", specialty: "", category: "", insurance: "" };

const FiltersContext = createContext(null);

/** Global dashboard filters (report §۷), shared across every analytics page
 *  so switching pages keeps the current selection. */
export function FiltersProvider({ children }) {
  const [filters, setFilters] = useState(EMPTY);

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

  const value = useMemo(
    () => ({ filters, set, reset, queryString, activeCount }),
    [filters, set, reset, queryString, activeCount],
  );

  return <FiltersContext.Provider value={value}>{children}</FiltersContext.Provider>;
}

export function useFilters() {
  const ctx = useContext(FiltersContext);
  if (!ctx) throw new Error("useFilters must be used inside <FiltersProvider>");
  return ctx;
}
