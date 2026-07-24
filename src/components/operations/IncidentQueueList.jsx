import Badge from '@/components/common/Badge.jsx';
import EmptyState from '@/components/common/EmptyState.jsx';
import { ShieldAlert } from 'lucide-react';

const PRIORITY_TONE = { CRITICAL: 'critical', HIGH: 'warning', ELEVATED: 'warning', ROUTINE: 'neutral' };
const PRIORITY_BORDER = {
  CRITICAL: 'border-l-status-critical',
  HIGH: 'border-l-status-warning',
  ELEVATED: 'border-l-status-warning',
  ROUTINE: 'border-l-border-strong',
};

/**
 * "Incident Queue" panel on the Tactical Deployment Center — priority-
 * ranked list (CRITICAL/HIGH/ELEVATED/ROUTINE) with zone and required-team
 * detail, per the Figma.
 */
export default function IncidentQueueList({ incidents = [] }) {
  if (incidents.length === 0) {
    return <EmptyState icon={ShieldAlert} title="No active incidents" message="The queue is currently clear." />;
  }

  return (
    <ul className="flex flex-col gap-3">
      {incidents.map((incident) => (
        <li
          key={incident.id}
          className={`border-l-2 pl-3 py-1 ${PRIORITY_BORDER[incident.priority] ?? PRIORITY_BORDER.ROUTINE}`}
        >
          <div className="flex items-center justify-between flex-wrap gap-2">
            <span className="label-eyebrow">{incident.id}</span>
            <span className="text-xs font-mono text-ink-muted">{incident.timestamp}</span>
          </div>
          <div className="flex items-center gap-2 mt-1">
            <Badge tone={PRIORITY_TONE[incident.priority] ?? 'neutral'}>{incident.priority}</Badge>
            <p className="text-sm text-ink-primary">{incident.title}</p>
          </div>
          <p className="text-xs text-ink-muted mt-1">{incident.zone}</p>
          <div className="flex items-center justify-between mt-1.5 text-xs">
            {incident.requiredTeam && <span className="text-ink-muted">REQ: {incident.requiredTeam}</span>}
            <span className="font-mono text-ink-secondary ml-auto">{incident.assignment}</span>
          </div>
        </li>
      ))}
    </ul>
  );
}
