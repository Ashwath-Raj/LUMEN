/**
 * "Field Operatives 84/120" / "Tactical Vehicles 12/15" style labeled
 * progress bar used in the Tactical Deployment Center's Resource Metrics
 * panel.
 */
export default function ResourceMetricBar({ label, current, total, footnotes = [] }) {
  const pct = total > 0 ? Math.round((current / total) * 100) : 0;

  return (
    <div>
      <div className="flex items-baseline justify-between">
        <span className="label-eyebrow">{label}</span>
        <span className="font-display text-2xl">
          {current}
          <span className="text-ink-muted text-base">/{total}</span>
        </span>
      </div>
      <div className="h-1.5 rounded-full bg-surface-2 overflow-hidden mt-2">
        <div className="h-full bg-accent-gold" style={{ width: `${pct}%` }} />
      </div>
      {footnotes.length > 0 && (
        <div className="flex justify-between text-xs text-ink-muted mt-1.5">
          {footnotes.map((note) => (
            <span key={note}>{note}</span>
          ))}
        </div>
      )}
    </div>
  );
}
