const TREND_TONE = {
  critical: 'text-status-critical',
  warning: 'text-status-warning',
  success: 'text-status-success',
  neutral: 'text-ink-muted',
};

/**
 * "Active Patrols / 42 / +12% shift" style card. Reused on Command Center,
 * Tactical Deployment, Governance & Security. `trend`/`trendTone`/`footer`
 * are optional so one component covers all three contexts.
 */
export default function StatCard({ eyebrow, label, value, trend, trendTone = 'neutral', footer }) {
  return (
    <div className="panel p-4">
      {eyebrow && <p className="label-eyebrow mb-1">{eyebrow}</p>}
      <p className="text-ink-secondary text-sm">{label}</p>
      <div className="flex items-baseline gap-2 mt-1">
        <span className="font-display text-3xl">{value}</span>
        {trend && <span className={`text-xs ${TREND_TONE[trendTone]}`}>{trend}</span>}
      </div>
      {footer}
    </div>
  );
}
