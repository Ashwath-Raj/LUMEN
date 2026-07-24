import { ChevronDown } from 'lucide-react';

/**
 * Styled select used by Filter Criteria (Geospatial), and future dropdown
 * filters elsewhere. Native <select> under the hood for accessibility.
 */
export default function Select({ id, label, value, onChange, options = [] }) {
  return (
    <div className="flex flex-col gap-1.5">
      {label && (
        <label htmlFor={id} className="label-eyebrow">
          {label}
        </label>
      )}
      <div className="relative">
        <select
          id={id}
          value={value}
          onChange={(e) => onChange?.(e.target.value)}
          className="w-full appearance-none bg-surface-2 border border-border-subtle rounded-sm pl-3 pr-8 py-2 text-sm text-ink-primary focus:border-accent-gold outline-none transition-colors"
        >
          {options.map((opt) => (
            <option key={opt} value={opt}>
              {opt}
            </option>
          ))}
        </select>
        <ChevronDown
          size={14}
          className="absolute right-2.5 top-1/2 -translate-y-1/2 text-ink-muted pointer-events-none"
        />
      </div>
    </div>
  );
}
