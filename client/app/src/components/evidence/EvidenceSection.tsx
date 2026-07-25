/**
 * `EvidenceSection` (D3) — a labelled group of §8 evidence, the "how do we know"
 * answer (§A question 3). Renders as a chip row (default, compact) or expandable
 * rows (`variant="rows"`, for dense/inspector contexts).
 *
 * Per-item restriction (§4.2) is delegated to an optional `restrictedFor`
 * predicate the caller supplies from role + evidence classification; by default
 * nothing is masked (the backend already scopes what it returns, and masking is
 * applied where role is known). Empty evidence renders an explicit note, never a
 * blank region.
 */
import { EvidenceChip } from "./EvidenceChip";
import { EvidenceRow } from "./EvidenceRow";
import type { Evidence } from "@/types/contracts";

interface EvidenceSectionProps {
  evidence: Evidence[];
  /** Return true to mask an item for the current viewer (§4.2). */
  restrictedFor?: (evidence: Evidence) => boolean;
  onActivate?: (evidence: Evidence) => void;
  variant?: "chips" | "rows";
  /** Section label; omit to render just the items. */
  label?: string;
}

export function EvidenceSection({
  evidence,
  restrictedFor,
  onActivate,
  variant = "chips",
  label = "Evidence",
}: EvidenceSectionProps) {
  return (
    <section aria-label={label} className="flex flex-col gap-2">
      {label ? (
        <h4 className="text-caption uppercase tracking-wide text-ink-muted">
          {label}
        </h4>
      ) : null}

      {evidence.length === 0 ? (
        <p className="text-caption text-ink-faint">
          No linked evidence for this item.
        </p>
      ) : variant === "rows" ? (
        <div className="flex flex-col">
          {evidence.map((item) => (
            <EvidenceRow
              key={`${item.entity}:${item.id}`}
              evidence={item}
              restricted={restrictedFor?.(item) ?? false}
              onActivate={onActivate}
            />
          ))}
        </div>
      ) : (
        <div className="flex flex-wrap gap-2">
          {evidence.map((item) => (
            <EvidenceChip
              key={`${item.entity}:${item.id}`}
              evidence={item}
              restricted={restrictedFor?.(item) ?? false}
              onActivate={onActivate}
            />
          ))}
        </div>
      )}
    </section>
  );
}
