import { useState } from 'react';
import { ChevronDown, ShieldAlert } from 'lucide-react';

const TONE_ICON_COLOR = {
  critical: 'text-status-critical',
  warning: 'text-status-warning',
  neutral: 'text-ink-muted',
};

/**
 * Expandable "Forensic Audit Log" row — collapsed shows title/timestamp,
 * expanded reveals the routine-activity detail text, per the Figma's
 * "Unauthorized Geospatial Access Attempt" entry.
 */
export default function AuditLogEntry({ title, timestamp, detail, tone = 'neutral', origin }) {
  const [expanded, setExpanded] = useState(false);

  return (
    <li className="border-b border-border-subtle last:border-b-0">
      <button
        type="button"
        onClick={() => setExpanded((v) => !v)}
        aria-expanded={expanded}
        className="w-full flex items-center justify-between gap-3 py-3 text-left"
      >
        <div className="flex items-center gap-2.5 min-w-0">
          <ShieldAlert size={15} className={`shrink-0 ${TONE_ICON_COLOR[tone]}`} />
          <div className="min-w-0">
            <p className="text-sm text-ink-primary truncate">{title}</p>
            <p className="text-xs text-ink-muted font-mono">
              {timestamp} · {origin}
            </p>
          </div>
        </div>
        <ChevronDown
          size={15}
          className={`shrink-0 text-ink-muted transition-transform ${expanded ? 'rotate-180' : ''}`}
        />
      </button>
      {expanded && <p className="text-xs text-ink-muted pb-3 pl-6 leading-relaxed">{detail}</p>}
    </li>
  );
}
