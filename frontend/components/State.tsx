export function Loading({ label = 'Loading…' }: { label?: string }) {
  return (
    <div className="flex items-center gap-3 py-10 text-muted">
      <span className="inline-block h-4 w-4 animate-spin rounded-full border-2 border-grass-500 border-t-transparent" />
      {label}
    </div>
  );
}

export function ErrorBox({ message, onRetry }: { message: string; onRetry?: () => void }) {
  return (
    <div className="card border-red-500/40 bg-red-500/5">
      <div className="flex items-start gap-3">
        <span className="text-2xl">⚠️</span>
        <div className="flex-1">
          <div className="font-semibold text-red-200">Something went wrong</div>
          <div className="mt-1 text-sm text-muted">{message}</div>
          {onRetry && (
            <button onClick={onRetry} className="btn-ghost mt-3">Try again</button>
          )}
        </div>
      </div>
    </div>
  );
}

export function Empty({ message }: { message: string }) {
  return (
    <div className="card text-center text-muted">
      <div className="mb-1 text-3xl">🍃</div>
      {message}
    </div>
  );
}

/** Convenience wrapper: render loading / error / children. */
export function Async<T>({ state, children, retryLabel }:
  { state: { data: T | null; error: string | null; loading: boolean; reload: () => void };
    children: (data: T) => React.ReactNode; retryLabel?: string }) {
  if (state.loading && state.data === null) return <Loading label={retryLabel} />;
  if (state.error) return <ErrorBox message={state.error} onRetry={state.reload} />;
  if (state.data === null) return <Loading />;
  return <>{children(state.data)}</>;
}
