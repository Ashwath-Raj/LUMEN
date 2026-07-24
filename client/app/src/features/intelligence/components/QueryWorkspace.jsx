import { useState } from 'react';
import { Send } from 'lucide-react';

/**
 * "Query Workspace" panel — natural-language investigation query input,
 * plus a short history of previously submitted queries this session.
 */
export default function QueryWorkspace({ history = [], onSubmit, isSubmitting }) {
  const [value, setValue] = useState('');

  const handleSubmit = (e) => {
    e.preventDefault();
    if (!value.trim()) return;
    onSubmit?.(value.trim());
    setValue('');
  };

  return (
    <div className="panel p-4 flex flex-col gap-3">
      <h3 className="font-display text-lg">Query Workspace</h3>
      <form onSubmit={handleSubmit} className="flex gap-2">
        <input
          value={value}
          onChange={(e) => setValue(e.target.value)}
          placeholder="Enter investigation parameters or natural language query..."
          className="flex-1 bg-surface-2 border border-border-subtle rounded-sm px-3 py-2 text-sm text-ink-primary placeholder:text-ink-muted focus:border-accent-gold outline-none transition-colors"
        />
        <button
          type="submit"
          disabled={isSubmitting || !value.trim()}
          aria-label="Submit query"
          className="w-10 h-10 shrink-0 rounded-sm bg-accent-gold text-surface-0 flex items-center justify-center disabled:opacity-50 hover:bg-accent-goldMuted transition-colors"
        >
          <Send size={15} />
        </button>
      </form>

      {history.length > 0 && (
        <ul className="flex flex-col gap-1.5 mt-1">
          {history.map((entry) => (
            <li key={entry.id} className="text-xs text-ink-muted flex gap-2">
              <span className="font-mono shrink-0">{entry.timestamp}</span>
              <span className="truncate">{entry.query}</span>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
