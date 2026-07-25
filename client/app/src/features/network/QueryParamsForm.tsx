/**
 * Parameter slots for the §14.4 named queries (E.6: "parameter slots on
 * selection"). Only the params the selected query actually accepts are shown —
 * the backend rejects a missing required param with 422, so the form marks them
 * required and disables Run until they are supplied.
 *
 * Person pickers are populated from the REAL `/persons` list; district and case
 * inputs take the ids those surfaces expose.
 */
import { usePersons } from "@/api";
import type { NetworkQueryParams } from "@/api";
import { Button } from "@/design/primitives";
import { QUERY_PARAMS } from "./queryParams";


interface QueryParamsFormProps {
  queryId: string;
  value: NetworkQueryParams;
  onChange: (next: NetworkQueryParams) => void;
  onRun: () => void;
}

const INPUT =
  "w-full rounded border border-line bg-void px-2 py-1.5 text-caption text-ink-primary outline-none focus:border-signal/50";

export function QueryParamsForm({ queryId, value, onChange, onRun }: QueryParamsFormProps) {
  const needed = QUERY_PARAMS[queryId] ?? [];
  const persons = usePersons(200, 0);
  const options = persons.data?.persons ?? [];

  if (needed.length === 0) {
    return (
      <div className="flex items-center gap-2 border-b border-line px-4 py-2">
        <span className="text-caption text-ink-faint">No parameters required.</span>
        <Button variant="primary" className="ml-auto" onClick={onRun}>
          Run {queryId.toUpperCase()}
        </Button>
      </div>
    );
  }

  const missing = needed.some((k) => {
    const v = value[k];
    return v === undefined || v === "" || (Array.isArray(v) && v.length === 0);
  });

  function personSelect(key: "person_a" | "person_b", label: string) {
    return (
      <label key={key} className="flex min-w-[180px] flex-1 flex-col gap-1">
        <span className="text-caption text-ink-muted">{label}</span>
        <select
          className={INPUT}
          value={(value[key] as string) ?? ""}
          onChange={(e) => onChange({ ...value, [key]: e.target.value })}
        >
          <option value="">Select a person…</option>
          {options.map((p) => (
            <option key={p.person_id} value={p.person_id}>
              {p.canonical_name}
            </option>
          ))}
        </select>
      </label>
    );
  }

  function groupSelect(key: "group_a" | "group_b", label: string) {
    const selected = (value[key] as string[]) ?? [];
    return (
      <label key={key} className="flex min-w-[180px] flex-1 flex-col gap-1">
        <span className="text-caption text-ink-muted">{label}</span>
        <select
          multiple
          size={4}
          className={INPUT}
          value={selected}
          onChange={(e) =>
            onChange({
              ...value,
              [key]: [...e.target.selectedOptions].map((o) => o.value),
            })
          }
        >
          {options.map((p) => (
            <option key={p.person_id} value={p.person_id}>
              {p.canonical_name}
            </option>
          ))}
        </select>
      </label>
    );
  }

  return (
    <div className="flex flex-wrap items-end gap-3 border-b border-line px-4 py-3">
      {needed.map((key) => {
        if (key === "person_a") return personSelect("person_a", "Person A");
        if (key === "person_b") return personSelect("person_b", "Person B");
        if (key === "group_a") return groupSelect("group_a", "Group A");
        if (key === "group_b") return groupSelect("group_b", "Group B");
        if (key === "district_id")
          return (
            <label key={key} className="flex w-40 flex-col gap-1">
              <span className="text-caption text-ink-muted">District ID</span>
              <input
                type="number"
                className={INPUT}
                value={value.district_id ?? ""}
                onChange={(e) =>
                  onChange({ ...value, district_id: Number(e.target.value) || undefined })
                }
              />
            </label>
          );
        if (key === "case_id")
          return (
            <label key={key} className="flex w-40 flex-col gap-1">
              <span className="text-caption text-ink-muted">Case ID</span>
              <input
                type="number"
                className={INPUT}
                value={value.case_id ?? ""}
                onChange={(e) =>
                  onChange({ ...value, case_id: Number(e.target.value) || undefined })
                }
              />
            </label>
          );
        if (key === "top_n")
          return (
            <label key={key} className="flex w-32 flex-col gap-1">
              <span className="text-caption text-ink-muted">Top N</span>
              <input
                type="number"
                min={1}
                max={50}
                className={INPUT}
                value={value.top_n ?? 10}
                onChange={(e) => onChange({ ...value, top_n: Number(e.target.value) || 10 })}
              />
            </label>
          );
        if (key === "as_of")
          return (
            <label key={key} className="flex w-44 flex-col gap-1">
              <span className="text-caption text-ink-muted">As of</span>
              <input
                type="date"
                className={INPUT}
                value={value.as_of ?? ""}
                onChange={(e) => onChange({ ...value, as_of: e.target.value || undefined })}
              />
            </label>
          );
        return null;
      })}
      <Button variant="primary" onClick={onRun} disabled={missing}>
        Run {queryId.toUpperCase()}
      </Button>
    </div>
  );
}
