export interface Seg { label: string; value: number; color: string; }

/** A single stacked probability bar with an optional legend. */
export function ProbBar({ segments, showLegend = true }:
                        { segments: Seg[]; showLegend?: boolean }) {
  const total = segments.reduce((s, x) => s + x.value, 0) || 1;
  return (
    <div className="space-y-1.5">
      <div className="probbar flex">
        {segments.map((s, i) => (
          <span key={i} style={{ width: `${(s.value / total) * 100}%`, background: s.color }} />
        ))}
      </div>
      {showLegend && (
        <div className="flex flex-wrap gap-x-4 gap-y-1 text-xs text-muted">
          {segments.map((s, i) => (
            <span key={i} className="flex items-center gap-1.5">
              <span className="h-2 w-2 rounded-full" style={{ background: s.color }} />
              {s.label} <span className="text-ink font-semibold">{Math.round(s.value * 100)}%</span>
            </span>
          ))}
        </div>
      )}
    </div>
  );
}

/** Horizontal labelled meter (for sim outcomes etc.) */
export function Meter({ value, color = '#16c784' }: { value: number; color?: string }) {
  return (
    <div className="probbar">
      <span style={{ width: `${Math.min(100, value * 100)}%`, background: color }} />
    </div>
  );
}
