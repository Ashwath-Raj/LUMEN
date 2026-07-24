import { useState } from 'react';
import { ArrowUpRight, Check } from 'lucide-react';

/**
 * "Actionable Directives" list item — a suggested next step the AI has
 * surfaced (deploy surveillance, subpoena records, etc). Acknowledging it
 * is a local UI action for now; wiring to a real workflow endpoint is a
 * backend decision for later.
 */
export default function ActionableDirectiveCard({ label }) {
  const [acknowledged, setAcknowledged] = useState(false);

  return (
    <li className="flex items-center justify-between gap-3 py-2 border-b border-border-subtle last:border-b-0">
      <span className={`text-sm ${acknowledged ? 'text-ink-muted line-through' : 'text-ink-secondary'}`}>
        {label}
      </span>
      <button
        type="button"
        onClick={() => setAcknowledged((v) => !v)}
        aria-pressed={acknowledged}
        className={`shrink-0 w-7 h-7 rounded-sm border flex items-center justify-center transition-colors ${
          acknowledged
            ? 'border-status-success text-status-success bg-status-successSoft'
            : 'border-border-strong text-ink-muted hover:text-accent-gold hover:border-accent-gold'
        }`}
        aria-label={acknowledged ? 'Mark as pending' : 'Acknowledge directive'}
      >
        {acknowledged ? <Check size={13} /> : <ArrowUpRight size={13} />}
      </button>
    </li>
  );
}
