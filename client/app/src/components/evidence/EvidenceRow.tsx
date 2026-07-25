/**
 * `EvidenceRow` (D3) — an evidence item in row form with expandable metadata,
 * for dense contexts (timelines, the inspector, evidence lists) where a chip row
 * is too terse. Shows the typed glyph + label as the primary link, with the
 * entity type and canonical id (mono) revealed on expand.
 *
 * Reuses `EvidenceChip` for the link + restricted behaviour so there is one
 * implementation of "evidence is a link / evidence can be masked" (§8, §4.2).
 */
import { useState } from "react";
import { ChevronDown, ChevronRight } from "lucide-react";

import { EvidenceChip } from "./EvidenceChip";
import type { Evidence } from "@/types/contracts";
import { cn } from "@/utils/cn";

interface EvidenceRowProps {
  evidence: Evidence;
  restricted?: boolean;
  onActivate?: (evidence: Evidence) => void;
}

export function EvidenceRow({
  evidence,
  restricted = false,
  onActivate,
}: EvidenceRowProps) {
  const [open, setOpen] = useState(false);

  return (
    <div className="flex flex-col gap-1 border-b border-line/60 py-2 last:border-b-0">
      <div className="flex items-center gap-2">
        {!restricted ? (
          <button
            type="button"
            onClick={() => setOpen((v) => !v)}
            aria-expanded={open}
            aria-label={open ? "Hide metadata" : "Show metadata"}
            className="text-ink-faint hover:text-ink-muted"
          >
            {open ? (
              <ChevronDown size={14} aria-hidden />
            ) : (
              <ChevronRight size={14} aria-hidden />
            )}
          </button>
        ) : (
          <span className="w-[14px]" aria-hidden />
        )}
        <EvidenceChip
          evidence={evidence}
          restricted={restricted}
          onActivate={onActivate}
        />
      </div>
      {open && !restricted ? (
        <dl
          className={cn(
            "ml-6 grid grid-cols-[auto_1fr] gap-x-3 gap-y-0.5",
            "text-caption text-ink-muted",
          )}
        >
          <dt className="text-ink-faint">type</dt>
          <dd>{evidence.entity}</dd>
          <dt className="text-ink-faint">id</dt>
          <dd className="font-mono">{evidence.id}</dd>
        </dl>
      ) : null}
    </div>
  );
}
