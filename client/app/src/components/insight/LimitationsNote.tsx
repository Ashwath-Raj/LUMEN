/**
 * `LimitationsNote` (part of D1) — the §8 `limitations`, the "what this cannot
 * tell you" answer (§A question 5, §11 gate 4). Limitations are NEVER empty (§8
 * invariant 2), so this component treats an empty list as a defect and says so
 * rather than rendering nothing — the invariant must be visible if a bad payload
 * ever slips the backend guard.
 */
import { AlertTriangle } from "lucide-react";

interface LimitationsNoteProps {
  limitations: string[];
}

export function LimitationsNote({ limitations }: LimitationsNoteProps) {
  const items = limitations.filter((s) => s.trim());
  return (
    <section aria-label="Limitations" className="flex flex-col gap-1">
      <h4 className="flex items-center gap-1.5 text-caption uppercase tracking-wide text-ink-muted">
        <AlertTriangle size={12} strokeWidth={1.5} aria-hidden />
        Limitations
      </h4>
      {items.length === 0 ? (
        <p className="text-caption text-risk-high">
          Missing limitations — every insight must state what it cannot tell you
          (§8 invariant 2).
        </p>
      ) : (
        <ul className="list-disc pl-4 text-caption text-ink-muted">
          {items.map((limitation, i) => (
            <li key={i}>{limitation}</li>
          ))}
        </ul>
      )}
    </section>
  );
}
