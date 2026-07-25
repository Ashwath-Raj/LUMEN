/**
 * `FilterBar` (D11) — the one declarative filter bar (arch D11 "One
 * implementation"). Given a field config + current values, it renders:
 *   - a full-text `q` slot (arch D11 "full-text q slot"),
 *   - a removable chip per active filter (arch D11 "chips for active filters"),
 *   - an "Add filter" menu bound to the config's fields (arch D11 "add-filter
 *     menu bound to the endpoint's params").
 *
 * It is CONTROLLED and URL-agnostic: it calls `onChange(key, value)` and the
 * page writes the value to the URL (arch §C "URL is state"). This keeps the
 * FilterBar reusable across `/cases`, `/anomalies`, the insight feed and
 * `/quality` — none of which it knows about.
 *
 * A11y: the add-filter menu is a real disclosure (Esc closes, click-outside
 * closes, aria-expanded); chips have accessible remove buttons; the search field
 * is a labelled form that submits on Enter.
 */
import { useEffect, useRef, useState } from "react";
import { Search, Plus, X } from "lucide-react";

import { Panel } from "@/design/primitives";
import { cn } from "@/utils/cn";
import type { FilterField, FilterValues } from "./types";
import { FilterFieldEditor } from "./FilterFieldEditor";

interface FilterBarProps {
  fields: FilterField[];
  values: FilterValues;
  /** Set/clear a single filter value (empty/undefined clears it). */
  onChange: (key: string, value: string | undefined) => void;
  /** The full-text q value + setter (separate slot from the chips). */
  q: string;
  onSearch: (q: string) => void;
  /** Clear every active filter (and q). */
  onClearAll?: () => void;
}

export function FilterBar({
  fields,
  values,
  onChange,
  q,
  onSearch,
  onClearAll,
}: FilterBarProps) {
  const [menuOpen, setMenuOpen] = useState(false);
  const [editing, setEditing] = useState<FilterField | null>(null);
  const [qDraft, setQDraft] = useState(q);
  const menuRef = useRef<HTMLDivElement>(null);

  useEffect(() => setQDraft(q), [q]);

  useEffect(() => {
    if (!menuOpen) return;
    function onDoc(e: MouseEvent) {
      if (menuRef.current && !menuRef.current.contains(e.target as Node)) {
        setMenuOpen(false);
        setEditing(null);
      }
    }
    function onKey(e: KeyboardEvent) {
      if (e.key === "Escape") {
        setMenuOpen(false);
        setEditing(null);
      }
    }
    document.addEventListener("mousedown", onDoc);
    document.addEventListener("keydown", onKey);
    return () => {
      document.removeEventListener("mousedown", onDoc);
      document.removeEventListener("keydown", onKey);
    };
  }, [menuOpen]);

  const activeChips = fields
    .map((field) => {
      if (field.kind === "daterange" && field.rangeKeys) {
        const from = values[field.rangeKeys.from];
        const to = values[field.rangeKeys.to];
        if (!from && !to) return null;
        const text = `${from ?? "…"} → ${to ?? "…"}`;
        return { field, display: `${field.label}: ${text}` };
      }
      const value = values[field.key];
      if (!value) return null;
      const shown = field.formatValue ? field.formatValue(value) : value;
      return { field, display: `${field.label}: ${shown}` };
    })
    .filter((c): c is { field: FilterField; display: string } => c !== null);

  function clearField(field: FilterField) {
    if (field.kind === "daterange" && field.rangeKeys) {
      onChange(field.rangeKeys.from, undefined);
      onChange(field.rangeKeys.to, undefined);
    } else {
      onChange(field.key, undefined);
    }
  }

  const hasActive = activeChips.length > 0 || q.length > 0;

  return (
    <div className="flex flex-col gap-2">
      <div className="flex items-center gap-2">
        {/* Full-text q slot */}
        <form
          className="flex flex-1 items-center gap-2 rounded border border-line bg-void px-3 py-2"
          onSubmit={(e) => {
            e.preventDefault();
            onSearch(qDraft.trim());
          }}
          role="search"
        >
          <Search size={16} className="text-ink-faint" aria-hidden />
          <input
            type="text"
            value={qDraft}
            onChange={(e) => setQDraft(e.target.value)}
            placeholder="Search cases — CrimeNo, title, brief facts…"
            aria-label="Search cases"
            className="flex-1 bg-transparent text-body text-ink-primary outline-none placeholder:text-ink-faint"
          />
          {qDraft ? (
            <button
              type="button"
              onClick={() => {
                setQDraft("");
                onSearch("");
              }}
              aria-label="Clear search"
              className="text-ink-faint hover:text-ink-primary"
            >
              <X size={14} />
            </button>
          ) : null}
        </form>

        {/* Add-filter menu */}
        <div ref={menuRef} className="relative">
          <button
            type="button"
            onClick={() => setMenuOpen((v) => !v)}
            aria-haspopup="menu"
            aria-expanded={menuOpen}
            className="flex items-center gap-1 rounded border border-line px-3 py-2 text-body text-ink-muted hover:border-signal/40 hover:text-ink-primary"
          >
            <Plus size={16} aria-hidden />
            Add filter
          </button>

          {menuOpen ? (
            <Panel
              elevated
              role="menu"
              className="absolute right-0 top-full z-overlay mt-2 w-72"
            >
              {editing ? (
                <FilterFieldEditor
                  field={editing}
                  value={values[editing.key] ?? ""}
                  rangeValue={
                    editing.rangeKeys
                      ? {
                          from: values[editing.rangeKeys.from] ?? "",
                          to: values[editing.rangeKeys.to] ?? "",
                        }
                      : undefined
                  }
                  onApply={(patch) => {
                    for (const [k, v] of Object.entries(patch)) onChange(k, v);
                    setEditing(null);
                    setMenuOpen(false);
                  }}
                  onCancel={() => setEditing(null)}
                />
              ) : (
                <ul className="max-h-72 overflow-auto py-1">
                  {fields.map((field) => (
                    <li key={field.key}>
                      <button
                        type="button"
                        role="menuitem"
                        onClick={() => setEditing(field)}
                        className="flex w-full items-center px-4 py-2 text-left text-body text-ink-muted hover:bg-raised hover:text-ink-primary"
                      >
                        {field.label}
                      </button>
                    </li>
                  ))}
                </ul>
              )}
            </Panel>
          ) : null}
        </div>
      </div>

      {/* Active filter chips */}
      {hasActive ? (
        <div className="flex flex-wrap items-center gap-2">
          {activeChips.map(({ field, display }) => (
            <span
              key={field.key}
              className="inline-flex items-center gap-1 rounded border border-signal/40 bg-raised px-2 py-1 text-caption text-ink-primary"
            >
              {display}
              <button
                type="button"
                onClick={() => clearField(field)}
                aria-label={`Remove ${field.label} filter`}
                className="text-ink-faint hover:text-ink-primary"
              >
                <X size={12} />
              </button>
            </span>
          ))}
          {onClearAll ? (
            <button
              type="button"
              onClick={onClearAll}
              className={cn(
                "text-caption text-ink-faint underline hover:text-ink-primary",
              )}
            >
              Clear all
            </button>
          ) : null}
        </div>
      ) : null}
    </div>
  );
}
