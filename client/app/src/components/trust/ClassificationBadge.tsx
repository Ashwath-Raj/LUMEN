/**
 * `ClassificationBadge` (D12) — the §4.1 governance class of a record or insight
 * (PUBLIC · INTERNAL · CONFIDENTIAL · RESTRICTED). Governance is rendered, not
 * claimed (§11, §B): the class is always visible on anything that carries one.
 *
 * RESTRICTED and CONFIDENTIAL read as governance signal (signal-tinted + lock),
 * not as alarm — they mean "handled correctly", the strongest trust cue
 * available (§B). PUBLIC/INTERNAL are neutral.
 */
import { Lock, Shield } from "lucide-react";

import { Badge } from "@/design/primitives/Badge";
import type { Classification } from "@/types/contracts";

interface ClassificationBadgeProps {
  classification: Classification;
}

const RESTRICTED_SET: ReadonlySet<Classification> = new Set([
  "CONFIDENTIAL",
  "RESTRICTED",
]);

const LABEL: Record<Classification, string> = {
  PUBLIC: "Public",
  INTERNAL: "Internal",
  CONFIDENTIAL: "Confidential",
  RESTRICTED: "Restricted",
};

export function ClassificationBadge({
  classification,
}: ClassificationBadgeProps) {
  const governed = RESTRICTED_SET.has(classification);
  return (
    <Badge
      tone={governed ? "var(--signal)" : undefined}
      icon={
        governed ? (
          <Lock size={12} strokeWidth={1.5} aria-hidden />
        ) : (
          <Shield size={12} strokeWidth={1.5} aria-hidden />
        )
      }
      title={`Classification: ${LABEL[classification]} (§4.1)`}
    >
      {LABEL[classification]}
    </Badge>
  );
}
