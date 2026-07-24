import { Link } from 'react-router-dom';
import Badge from '@/design/primitives/Badge.jsx';

/**
 * "Generated Leads" card — AI-surfaced lead with priority tag, description,
 * and links back into the source case(s) in Investigation.
 */
export default function GeneratedLeadCard({ priority, priorityTone, title, description, sourceCases = [] }) {
  return (
    <div className="panel p-3">
      <div className="flex items-center justify-between mb-1.5">
        <Badge tone={priorityTone}>{priority}</Badge>
      </div>
      <p className="font-display text-base leading-snug">{title}</p>
      <p className="text-ink-muted text-xs mt-1.5 leading-relaxed">{description}</p>
      {sourceCases.length > 0 && (
        <div className="flex gap-2 mt-2 flex-wrap">
          {sourceCases.map((caseLabel) => (
            <Link
              key={caseLabel}
              to="/investigation"
              className="text-[11px] font-mono text-accent-gold hover:underline"
            >
              {caseLabel}
            </Link>
          ))}
        </div>
      )}
    </div>
  );
}
