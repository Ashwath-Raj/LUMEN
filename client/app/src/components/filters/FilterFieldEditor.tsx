/**
 * `FilterFieldEditor` — the single-field editor inside the FilterBar add-filter
 * menu. Renders the control for the field's `kind` and applies a param patch on
 * confirm. A `select` with no options falls back to free-text entry, so
 * filtering works even before the lookups endpoint lands (the value still
 * round-trips through the URL). Kept separate from `FilterBar` so the bar stays
 * readable and this stays independently testable.
 */
import { useState } from "react";

import { Button } from "@/design/primitives";
import type { FilterField } from "./types";

interface FilterFieldEditorProps {
  field: FilterField;
  value: string;
  rangeValue?: { from: string; to: string };
  /** Apply a param patch (key → value|undefined). */
  onApply: (patch: Record<string, string | undefined>) => void;
  onCancel: () => void;
}

const INPUT_CLASS =
  "w-full rounded border border-line bg-void px-2 py-1.5 text-body text-ink-primary outline-none focus:border-signal/50";

export function FilterFieldEditor({
  field,
  value,
  rangeValue,
  onApply,
  onCancel,
}: FilterFieldEditorProps) {
  const [draft, setDraft] = useState(value);
  const [from, setFrom] = useState(rangeValue?.from ?? "");
  const [to, setTo] = useState(rangeValue?.to ?? "");

  function apply() {
    if (field.kind === "daterange" && field.rangeKeys) {
      onApply({
        [field.rangeKeys.from]: from || undefined,
        [field.rangeKeys.to]: to || undefined,
      });
      return;
    }
    onApply({ [field.key]: draft || undefined });
  }

  const hasOptions = field.kind === "select" && (field.options?.length ?? 0) > 0;

  return (
    <div className="flex flex-col gap-3 p-3">
      <label className="text-caption uppercase tracking-wide text-ink-muted">
        {field.label}
      </label>

      {field.kind === "daterange" && field.rangeKeys ? (
        <div className="flex flex-col gap-2">
          <input
            type="date"
            aria-label={`${field.label} from`}
            value={from}
            onChange={(e) => setFrom(e.target.value)}
            className={INPUT_CLASS}
          />
          <input
            type="date"
            aria-label={`${field.label} to`}
            value={to}
            onChange={(e) => setTo(e.target.value)}
            className={INPUT_CLASS}
          />
        </div>
      ) : hasOptions ? (
        <select
          aria-label={field.label}
          value={draft}
          onChange={(e) => setDraft(e.target.value)}
          className={INPUT_CLASS}
        >
          <option value="">Any</option>
          {field.options!.map((opt) => (
            <option key={opt.value} value={opt.value}>
              {opt.label}
            </option>
          ))}
        </select>
      ) : (
        <input
          type={field.kind === "date" ? "date" : "text"}
          aria-label={field.label}
          value={draft}
          onChange={(e) => setDraft(e.target.value)}
          placeholder={
            field.kind === "select" ? "Type a value…" : `Filter by ${field.label}`
          }
          className={INPUT_CLASS}
          autoFocus
        />
      )}

      <div className="flex justify-end gap-2">
        <Button variant="ghost" onClick={onCancel}>
          Cancel
        </Button>
        <Button variant="primary" onClick={apply}>
          Apply
        </Button>
      </div>
    </div>
  );
}
