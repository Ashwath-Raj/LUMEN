import { Check } from 'lucide-react';

/**
 * Styled checkbox used by Overlay Layers (Geospatial), and future
 * multi-select filter controls elsewhere in the app.
 */
export default function Checkbox({ id, label, checked, onChange }) {
  return (
    <label htmlFor={id} className="flex items-center gap-2.5 cursor-pointer select-none">
      <span className="relative flex items-center justify-center w-4 h-4 shrink-0">
        <input
          id={id}
          type="checkbox"
          checked={checked}
          onChange={(e) => onChange?.(e.target.checked)}
          className="peer appearance-none w-4 h-4 rounded-sm border border-border-strong bg-surface-2 checked:bg-accent-gold checked:border-accent-gold transition-colors"
        />
        <Check
          size={11}
          strokeWidth={3}
          className="absolute text-surface-0 opacity-0 peer-checked:opacity-100 pointer-events-none"
        />
      </span>
      <span className="text-sm text-ink-secondary">{label}</span>
    </label>
  );
}
