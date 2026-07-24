import { Search } from 'lucide-react';

export default function SearchInput({ placeholder = 'Search...', value, onChange }) {
  return (
    <div className="relative">
      <Search size={14} className="absolute left-2.5 top-1/2 -translate-y-1/2 text-ink-muted" />
      <input
        type="search"
        value={value}
        onChange={onChange}
        placeholder={placeholder}
        className="bg-surface-1 border border-border-subtle rounded-sm pl-8 pr-3 py-1.5 text-sm text-ink-primary placeholder:text-ink-muted w-64 focus:border-accent-gold outline-none transition-colors"
      />
    </div>
  );
}
