import { AlertOctagon, RotateCw } from 'lucide-react';
import Button from './Button.jsx';

/**
 * Standard inline error state for any panel/page whose data fetch failed.
 * Used via useAsyncData's `error` + `refetch` — see hooks/useAsyncData.js.
 */
export default function ErrorState({
  title = 'Unable to load data',
  message = 'The request could not be completed. Check your connection and retry.',
  onRetry,
}) {
  return (
    <div
      role="alert"
      className="panel flex flex-col items-center justify-center gap-3 p-8 text-center"
    >
      <AlertOctagon size={22} className="text-status-critical" strokeWidth={1.5} />
      <div>
        <p className="font-display text-lg">{title}</p>
        <p className="text-ink-muted text-sm mt-1">{message}</p>
      </div>
      {onRetry && (
        <Button variant="ghost" onClick={onRetry} className="flex items-center gap-2 mt-2">
          <RotateCw size={14} />
          Retry
        </Button>
      )}
    </div>
  );
}
