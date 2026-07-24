import EmptyState from '@/design/primitives/EmptyState.jsx';
import { Radio } from 'lucide-react';

const TONE_BORDER = {
  critical: 'border-l-status-critical',
  warning: 'border-l-status-warning',
  success: 'border-l-status-success',
  neutral: 'border-l-border-strong',
};

/**
 * "Coordination Log" / "Recent Alerts" real-time feed list, shared between
 * Command Center (Dashboard) and Tactical Deployment Center (Operations).
 * entries: [{ id, timestamp, message, detail?, tone? }]
 */
export default function ActivityLogFeed({ title, entries = [], liveIndicator = true }) {
  return (
    <div className="panel p-4">
      <div className="flex items-center justify-between mb-3">
        <h3 className="font-display text-lg">{title}</h3>
        {liveIndicator && (
          <span className="flex items-center gap-1 text-xs text-status-success">
            <Radio size={12} />
            LIVE FEED
          </span>
        )}
      </div>

      {entries.length === 0 ? (
        <EmptyState title="No recent activity" message="New entries will appear here in real time." />
      ) : (
        <ul className="flex flex-col gap-2.5">
          {entries.map((entry) => (
            <li
              key={entry.id}
              className={`border-l-2 pl-3 py-0.5 ${TONE_BORDER[entry.tone] ?? TONE_BORDER.neutral}`}
            >
              <div className="flex items-baseline gap-2">
                <span className="label-eyebrow">{entry.timestamp}</span>
                <span className="text-sm text-ink-primary">{entry.message}</span>
              </div>
              {entry.detail && <p className="text-xs text-ink-muted mt-0.5">{entry.detail}</p>}
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
