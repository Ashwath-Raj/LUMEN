const TONE_CLASSES = {
  critical: 'bg-status-criticalSoft text-status-critical',
  warning: 'bg-status-warningSoft text-status-warning',
  success: 'bg-status-successSoft text-status-success',
  info: 'bg-status-infoSoft text-status-info',
  neutral: 'bg-surface-2 text-ink-secondary',
};

/**
 * Small uppercase status tag — CRITICAL / INVESTIGATING / ROUTINE / ACTIVE /
 * ARMED / FLIGHT RISK all map to this with a `tone`.
 */
export default function Badge({ tone = 'neutral', children }) {
  return (
    <span
      className={`inline-block px-2 py-0.5 text-xs font-mono uppercase tracking-wide rounded-sm ${TONE_CLASSES[tone]}`}
    >
      {children}
    </span>
  );
}
