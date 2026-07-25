/**
 * `EvidencePanel` — the "how do we know" block of an AI answer: the §8 evidence
 * rendered by the shared `EvidenceSection` (D3 — every item a link, restricted
 * state supported) with a count header and an explicit unverified note when the
 * answer cites nothing (Part 7: "If information cannot be verified, explicitly
 * say so").
 */
import { EvidenceSection } from "@/components/evidence";
import type { Evidence } from "@/types/contracts";

interface EvidencePanelProps {
  evidence: Evidence[];
  onActivate?: (evidence: Evidence) => void;
}

export function EvidencePanel({ evidence, onActivate }: EvidencePanelProps) {
  if (evidence.length === 0) {
    return (
      <p className="rounded border border-degraded/40 px-3 py-2 text-caption text-degraded">
        No canonical records ground this answer — treat it as unverified.
      </p>
    );
  }
  return (
    <EvidenceSection
      label={`Evidence (${evidence.length})`}
      evidence={evidence}
      onActivate={onActivate}
    />
  );
}
