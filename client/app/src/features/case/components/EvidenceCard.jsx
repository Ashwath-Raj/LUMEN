import { PackageSearch } from 'lucide-react';

/**
 * "Service Weapon - 9mm / SERIAL NO. ..." style entry, used across
 * Evidence Locker (Investigation + Analytics) and evidence preview grids.
 */
export default function EvidenceCard({ itemId, name, serialNo, thumbnailUrl, isSelected, onClick }) {
  return (
    <button
      type="button"
      onClick={onClick}
      className={`panel p-3 text-left transition-colors ${
        isSelected ? 'border-accent-gold bg-accent-goldSoft' : 'hover:border-border-strong'
      }`}
    >
      <p className="label-eyebrow">{itemId}</p>
      <p className="font-display mt-1">{name}</p>
      <p className="text-ink-muted text-xs mt-0.5">SERIAL NO. {serialNo}</p>
      {thumbnailUrl ? (
        <img src={thumbnailUrl} alt={name} className="mt-2 w-full h-24 object-cover rounded-sm" />
      ) : (
        <div className="mt-2 w-full h-24 rounded-sm bg-surface-2 flex items-center justify-center">
          <PackageSearch size={20} className="text-ink-muted" strokeWidth={1.5} />
        </div>
      )}
    </button>
  );
}
