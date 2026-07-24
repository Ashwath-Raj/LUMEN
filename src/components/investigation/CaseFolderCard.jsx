import { Folder } from 'lucide-react';
import Badge from '@/components/common/Badge.jsx';

const STATUS_TONE = {
  ACTIVE: 'success',
  UNSOLVED: 'warning',
  CLOSED: 'neutral',
};

/**
 * Folder-icon card used in every case grid across the app: Analytics'
 * Case Files (selectable, shows a preview alongside), Investigation's
 * Active Cases (navigates straight to the Case Board), Administration
 * archives, etc. `isSelected` + `onClick` are optional so it works either
 * as a navigation link or a selectable list item.
 */
export default function CaseFolderCard({ caseId, label, status, meta, isSelected, onClick }) {
  return (
    <button
      type="button"
      onClick={onClick}
      className={`panel p-4 flex flex-col items-center gap-2 text-center transition-colors ${
        isSelected ? 'border-accent-gold bg-accent-goldSoft' : 'hover:border-border-strong'
      }`}
    >
      <Folder
        size={28}
        strokeWidth={1.25}
        className={isSelected ? 'text-accent-gold' : 'text-ink-secondary'}
      />
      <p className="text-sm text-ink-primary">{label ?? caseId}</p>
      {status && <Badge tone={STATUS_TONE[status] ?? 'neutral'}>{status}</Badge>}
      {meta && <p className="text-ink-muted text-xs">{meta}</p>}
    </button>
  );
}
