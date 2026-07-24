import { useEffect, useState, useCallback } from 'react';

/**
 * Small fetch wrapper used by page components:
 *
 *   const { data, isLoading, error, refetch } = useAsyncData(
 *     () => dashboardService.fetchCommandCenterSummary(),
 *     []
 *   );
 *
 * Keeps individual pages free of repeated useState/useEffect plumbing.
 */
export function useAsyncData(fetcher, deps = []) {
  const [data, setData] = useState(null);
  const [error, setError] = useState(null);
  const [isLoading, setIsLoading] = useState(true);

  const run = useCallback(() => {
    let cancelled = false;
    setIsLoading(true);
    fetcher()
      .then((result) => {
        if (!cancelled) setData(result);
      })
      .catch((err) => {
        if (!cancelled) setError(err);
      })
      .finally(() => {
        if (!cancelled) setIsLoading(false);
      });
    return () => {
      cancelled = true;
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, deps);

  useEffect(() => run(), [run]);

  return { data, error, isLoading, refetch: run };
}
