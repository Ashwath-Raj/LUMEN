import { UserRound } from 'lucide-react';
import Badge from '@/design/primitives/Badge.jsx';

/**
 * "ID-77A9-PER / Shetty, Rahul / Primary Suspect / FLIGHT RISK / ARMED"
 * card — used both pinned to the CorkboardCanvas and in list form on
 * Suspect Profiles pages.
 */
export default function SuspectDossierCard({ referenceId, name, role, tags = [], photoUrl }) {
  return (
    <div className="panel p-3 w-64 bg-surface-1">
      <div className="flex justify-between items-start">
        <span className="label-eyebrow">{referenceId}</span>
      </div>
      <div className="flex items-center gap-3 mt-2">
        {photoUrl ? (
          <img src={photoUrl} alt={name} className="w-12 h-12 object-cover rounded-sm" />
        ) : (
          <div className="w-12 h-12 rounded-sm bg-surface-2 flex items-center justify-center shrink-0">
            <UserRound size={20} className="text-ink-muted" strokeWidth={1.5} />
          </div>
        )}
        <div className="min-w-0">
          <p className="font-display text-lg leading-tight truncate">{name}</p>
          <p className="text-ink-muted text-xs">{role}</p>
        </div>
      </div>
      <div className="flex gap-2 mt-3 flex-wrap">
        {tags.map((tag) => (
          <Badge key={tag.label} tone={tag.tone}>
            {tag.label}
          </Badge>
        ))}
      </div>
    </div>
  );
}
