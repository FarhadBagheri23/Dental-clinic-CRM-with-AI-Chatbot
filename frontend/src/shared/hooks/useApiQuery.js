import { useCallback, useEffect, useState } from "react";

/**
 * Minimal data fetching: run `fetcher(signal)` whenever `deps` change, abort
 * the in-flight request on unmount or re-run.
 *
 * ponytail: deliberately not TanStack Query — this app has no cache
 * invalidation, optimistic updates, or refetch-on-focus requirements. Swap it
 * in if those appear.
 */
export function useApiQuery(fetcher, deps = []) {
  const [state, setState] = useState({ data: null, loading: true, error: null });

  const run = useCallback((signal) => {
    setState((s) => ({ ...s, loading: true, error: null }));
    return fetcher(signal)
      .then((data) => setState({ data, loading: false, error: null }))
      .catch((error) => {
        // An aborted request was superseded; showing its error would flash a
        // failure for a request nobody is waiting on any more.
        if (error.name === "AbortError") return;
        setState({ data: null, loading: false, error: error.message });
      });
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, deps);

  useEffect(() => {
    const controller = new AbortController();
    run(controller.signal);
    return () => controller.abort();
  }, [run]);

  return state;
}
