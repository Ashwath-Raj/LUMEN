export default function FormField({ label, htmlFor, error, children }) {
  return (
    <div className="flex flex-col gap-1">
      {label && (
        <label htmlFor={htmlFor} className="label-eyebrow">
          {label}
        </label>
      )}
      {children}
      {error && <span className="text-xs text-status-critical">{error}</span>}
    </div>
  );
}
