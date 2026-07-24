import { Plus } from 'lucide-react';
import { Link } from 'react-router-dom';
import { useAuth } from '@/app/hooks/useAuth.js';

/**
 * "OPERATOR_042 / District Fusion Center" style card pinned above every
 * module's sidebar nav, per the Figma, plus the "+ New Investigation"
 * primary action seen on the Investigation/Operations sidebars.
 */
export default function OperatorMiniProfile({ primaryAction }) {
  const { operator } = useAuth();

  const initials = (operator?.name ?? 'OP')
    .split(' ')
    .map((part) => part[0])
    .join('')
    .slice(0, 2)
    .toUpperCase();

  return (
    <div className="px-3 py-4 border-b border-border-subtle flex flex-col gap-3">
      <div className="flex items-center gap-3">
        <div className="w-9 h-9 rounded-full bg-surface-2 border border-border-subtle flex items-center justify-center font-mono text-xs text-ink-secondary shrink-0">
          {initials}
        </div>
        <div className="min-w-0">
          <p className="text-sm text-ink-primary truncate">{operator?.name ?? 'Operator'}</p>
          <p className="label-eyebrow truncate">{operator?.unit ?? 'Unassigned Unit'}</p>
        </div>
      </div>

      {primaryAction && (
        <Link
          to={primaryAction.to}
          className="flex items-center justify-center gap-1.5 text-xs font-medium border border-border-strong rounded-sm py-2 text-ink-secondary hover:border-accent-gold hover:text-accent-gold transition-colors"
        >
          <Plus size={13} />
          {primaryAction.label}
        </Link>
      )}
    </div>
  );
}
