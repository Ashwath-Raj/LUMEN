/**
 * `InsightCard` (D1) — the platform's core component. Built first; used
 * everywhere. It renders a §8 `Insight` such that the seven questions (§A) are
 * STRUCTURAL, not optional: the card cannot render without limitations, a
 * confidence value cannot appear without its breakdown, evidence is always a
 * link. Those invariants are enforced by composition here.
 *
 * Two variants (arch D1):
 *   - compact:  glyph · headline · lifecycle badge · ConfidenceMeter · expander.
 *               Used in feeds (Command live feed, Briefing top-insights, network
 *               result rail). Expandable in place — the subject never navigates
 *               away to see detail.
 *   - expanded: adds the recommendation (if any), factor bars, the confidence
 *               breakdown, counterfactuals, evidence, limitations, lineage, the
 *               default §11 trust caveat, and the feedback/approve footer.
 *
 * No layout assumptions are hardcoded: the card is width-fluid, sits in whatever
 * container the caller provides, and every section degrades independently
 * (missing evidence, empty counterfactuals, absent lineage sub-fields) without
 * crashing (quality req: no component crashes on partial data).
 *
 * `defaultExpanded` seeds the full variant; `variant="expanded"` forces it open
 * and hides the compact toggle (e.g. the Console report card, the Case Workspace
 * intelligence column).
 */
import { useState } from "react";
import { ChevronDown, ChevronRight } from "lucide-react";

import { Panel } from "@/design/primitives";
import { ENTITY_GLYPH } from "@/design/tokens";
import type { Evidence, Insight } from "@/types/contracts";
import { cn } from "@/utils/cn";

import {
  ConfidenceBreakdown,
  ConfidenceMeter,
  FactorBars,
} from "@/components/confidence";
import { EvidenceSection } from "@/components/evidence";
import { LifecycleBadge, TrustBadge, trustContextFor } from "@/components/trust";

import { CounterfactualsNote } from "./CounterfactualsNote";
import { InsightActions } from "./InsightActions";
import { INSIGHT_KIND_LABEL } from "./insightKind";
import { LimitationsNote } from "./LimitationsNote";
import { LineagePanel } from "./LineagePanel";
import { RecommendationSection } from "./RecommendationSection";

interface InsightCardProps {
  insight: Insight;
  /** "compact" is expandable in place; "expanded" is always fully open. */
  variant?: "compact" | "expanded";
  /** Seed the compact card open. Ignored when variant="expanded". */
  defaultExpanded?: boolean;
  /** Hide the feedback/approve footer (e.g. read-only embeds). */
  hideActions?: boolean;
  /** Mask predicate for evidence items (§4.2), passed to the evidence section. */
  restrictedFor?: (evidence: Evidence) => boolean;
  /** Activate an evidence item (e.g. open in InspectorPanel) in addition to nav. */
  onEvidenceActivate?: (evidence: Evidence) => void;
  className?: string;
}

export function InsightCard({
  insight,
  variant = "compact",
  defaultExpanded = false,
  hideActions = false,
  restrictedFor,
  onEvidenceActivate,
  className,
}: InsightCardProps) {
  const forcedOpen = variant === "expanded";
  const [open, setOpen] = useState(defaultExpanded);
  const [breakdownOpen, setBreakdownOpen] = useState(forcedOpen);

  const expanded = forcedOpen || open;
  const trustContext = trustContextFor(insight.kind);
  const isRecommendation = insight.kind === "recommendation";

  return (
    <Panel className={cn("flex flex-col gap-3 p-4", className)}>
      {/* ── Header: glyph · kind · headline · score · lifecycle ─────────── */}
      <div className="flex items-start gap-3">
        <span
          aria-hidden
          className="mt-0.5 text-panel-title leading-none text-signal"
          title={`${INSIGHT_KIND_LABEL[insight.kind]} insight`}
        >
          {ENTITY_GLYPH.insight}
        </span>

        <div className="flex min-w-0 flex-1 flex-col gap-1">
          <div className="flex items-center gap-2">
            <span className="text-caption uppercase tracking-wide text-ink-faint">
              {INSIGHT_KIND_LABEL[insight.kind]}
            </span>
            <LifecycleBadge state={insight.lifecycle_state} />
            {insight.score !== null ? (
              <span className="ml-auto font-mono text-caption text-ink-muted">
                score {insight.score.toFixed(2)}
              </span>
            ) : null}
          </div>
          <p className="text-body text-ink-primary">{insight.headline}</p>
        </div>

        {!forcedOpen ? (
          <button
            type="button"
            onClick={() => setOpen((v) => !v)}
            aria-expanded={expanded}
            aria-label={expanded ? "Collapse insight" : "Expand insight"}
            className="text-ink-faint hover:text-ink-primary"
          >
            {expanded ? (
              <ChevronDown size={16} aria-hidden />
            ) : (
              <ChevronRight size={16} aria-hidden />
            )}
          </button>
        ) : null}
      </div>

      {/* Confidence meter is always visible; it toggles the breakdown (§9/§A:
          a confidence value never appears without its breakdown available). */}
      <ConfidenceMeter
        breakdown={insight.confidence_breakdown}
        expanded={breakdownOpen}
        onToggle={() => setBreakdownOpen((v) => !v)}
      />
      {breakdownOpen ? (
        <ConfidenceBreakdown breakdown={insight.confidence_breakdown} />
      ) : null}

      {/* ── Expanded body ──────────────────────────────────────────────── */}
      {expanded ? (
        <div className="flex flex-col gap-4">
          {isRecommendation ? (
            <RecommendationSection headline={insight.headline} />
          ) : null}

          {insight.factors.length > 0 ? (
            <section aria-label="Factors" className="flex flex-col gap-1.5">
              <h4 className="text-caption uppercase tracking-wide text-ink-muted">
                Why
              </h4>
              <FactorBars factors={insight.factors} />
            </section>
          ) : null}

          <CounterfactualsNote counterfactuals={insight.counterfactuals} />

          <EvidenceSection
            evidence={insight.evidence}
            restrictedFor={restrictedFor}
            onActivate={onEvidenceActivate}
          />

          <LimitationsNote limitations={insight.limitations} />

          <LineagePanel lineage={insight.lineage} />

          {/* Default §11 trust caveat for the kind — rendered, not claimed. */}
          {trustContext ? <TrustBadge context={trustContext} /> : null}

          {!hideActions ? (
            <InsightActions
              insightId={insight.id}
              lifecycleState={insight.lifecycle_state}
            />
          ) : null}
        </div>
      ) : null}
    </Panel>
  );
}
