import { useCallback, useEffect, useRef, useState } from 'react';

export interface AsyncState<T> {
  data: T | undefined;
  loading: boolean;
  error: Error | null;
  reload: () => void;
}

/** Runs `load` on mount and on `reload`, ignoring results that arrive after unmount or a newer run. */
export function useAsync<T>(load: () => Promise<T>, deps: ReadonlyArray<unknown> = []): AsyncState<T> {
  const [data, setData] = useState<T | undefined>(undefined);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<Error | null>(null);
  const [tick, setTick] = useState(0);
  const runId = useRef(0);

  useEffect(() => {
    const id = (runId.current += 1);
    setLoading(true);
    setError(null);
    load()
      .then((result) => {
        if (runId.current !== id) return;
        setData(result);
        setLoading(false);
      })
      .catch((err: unknown) => {
        if (runId.current !== id) return;
        setError(err instanceof Error ? err : new Error(String(err)));
        setLoading(false);
      });
    return () => {
      runId.current += 1;
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [tick, ...deps]);

  const reload = useCallback(() => setTick((value) => value + 1), []);

  return { data, loading, error, reload };
}
