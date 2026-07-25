/**
 * `EvidenceChip` (D3) — one §8 `Evidence` item. An evidence chip is ALWAYS a
 * link (§8 invariant: "every evidence chip is clickable"); it renders the typed
 * entity glyph + label and navigates to `evidence.url`.
 *
 * RESTRICTED state (§4.2): when the viewer's role is below the masking threshold
 * for this evidence, the chip renders the lock glyph + "restricted" in
 * `--ink-faint` and is NOT a link — a masked value is never blank space (§31.2).
 * The restriction decision is made by the caller (from role + evidence
 * classification); this component only renders the two states.
 *
 * URLs are backend-relative app paths (e.g. `/case/123`); internal ones route
 * via react-router, external ones (rare — kb docs) open normally.
 */
import { Link } from "react-router-dom";
import { Lock } from "lucide-react";

import { EVIDENCE_GLYPH, type EvidenceEntity } from "@/design/tokens";
import type { Evidence } from "@/types/contracts";
import { cn } from "@/utils/cn";

interface EvidenceChipProps {
  evidence: Evidence;
  /** Viewer is below the masking threshold for this evidence (§4.2). */
  restricted?: boolean;
  /** Optional extra click handler (e.g. open in InspectorPanel) alongside nav. */
  onActivate?: (evidence: Evidence) => void;
  className?: string;
}

const CHIP_BASE =
  "inline-flex items-center gap-1.5 rounded border px-2 py-1 text-caption";

function isInternal(url: string): boolean {
  return url.startsWith("/");
}

export function EvidenceChip({
  evidence,
  restricted = false,
  onActivate,
  className,
}: EvidenceChipProps) {
  const glyph = EVIDENCE_GLYPH[evidence.entity as EvidenceEntity] ?? "◆";

  if (restricted) {
    return (
      <span
        className={cn(
          CHIP_BASE,
          "border-line/60 text-ink-faint",
          className,
        )}
        title="Restricted — outside your access; access is logged (§4.2)"
      >
        <Lock size={12} strokeWidth={1.5} aria-hidden />
        <span>restricted</span>
      </span>
    );
  }

  const content = (
    <>
      <span aria-hidden className="text-ink-muted">
        {glyph}
      </span>
      <span className="truncate">{evidence.label}</span>
    </>
  );

  const classes = cn(
    CHIP_BASE,
    "max-w-full border-line text-ink-primary",
    "hover:border-signal/50 hover:text-signal",
    className,
  );

  const handleClick = onActivate
    ? () => onActivate(evidence)
    : undefined;

  if (isInternal(evidence.url)) {
    return (
      <Link to={evidence.url} className={classes} onClick={handleClick}>
        {content}
      </Link>
    );
  }

  return (
    <a
      href={evidence.url}
      className={classes}
      onClick={handleClick}
      rel="noreferrer"
    >
      {content}
    </a>
  );
}
