/**
 * Standard empty state — "no active cases", "no evidence logged", etc.
 * `icon` accepts any lucide-react icon component for context.
 */
export default function EmptyState({ icon: Icon, title, message, action }) {
  return (
    <div className="panel flex flex-col items-center justify-center gap-2 p-10 text-center">
      {Icon && <Icon size={22} className="text-ink-muted mb-1" strokeWidth={1.5} />}
      <p className="font-display text-lg">{title}</p>
      {message && <p className="text-ink-muted text-sm max-w-sm">{message}</p>}
      {action}
    </div>
  );
}
