'use client';

import { useCallback, useEffect, useState } from 'react';
import { ApiError } from './api';

export interface AsyncState<T> {
  data: T | null;
  error: string | null;
  loading: boolean;
  reload: () => void;
}

/** Run an async fetcher with loading/error tracking and a manual reload. */
export function useFetch<T>(fn: () => Promise<T>, deps: unknown[]): AsyncState<T> {
  const [data, setData] = useState<T | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  // eslint-disable-next-line react-hooks/exhaustive-deps
  const run = useCallback(() => {
    let alive = true;
    setLoading(true); setError(null);
    fn()
      .then(d => { if (alive) setData(d); })
      .catch(e => { if (alive) setError(e instanceof ApiError ? e.message : String(e)); })
      .finally(() => { if (alive) setLoading(false); });
    return () => { alive = false; };
  }, deps);

  useEffect(() => run(), [run]);
  return { data, error, loading, reload: run };
}
