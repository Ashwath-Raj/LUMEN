/**
 * Toggle switch used by System Preferences (Operator Dossier) and any
 * future boolean settings elsewhere in the app.
 */
export default function Switch({ id, checked, onChange, label, description }) {
  return (
    <div className="flex items-center justify-between gap-4">
      <div>
        {label && (
          <label htmlFor={id} className="text-sm text-ink-primary cursor-pointer">
            {label}
          </label>
        )}
        {description && <p className="text-xs text-ink-muted mt-0.5">{description}</p>}
      </div>
      <button
        id={id}
        type="button"
        role="switch"
        aria-checked={checked}
        onClick={() => onChange?.(!checked)}
        className={`relative w-10 h-[22px] rounded-full shrink-0 transition-colors ${
          checked ? 'bg-accent-gold' : 'bg-surface-2 border border-border-strong'
        }`}
      >
        <span
          className={`absolute top-0.5 w-4 h-4 rounded-full bg-surface-0 transition-transform ${
            checked ? 'translate-x-[22px] bg-white' : 'translate-x-0.5'
          }`}
        />
      </button>
    </div>
  );
}
