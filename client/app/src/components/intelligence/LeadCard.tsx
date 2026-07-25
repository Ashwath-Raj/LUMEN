/**
 * `LeadCard` — one intelligence lead (Part 3): priority · confidence · risk ·
 * related entities · reasoning · suggested next actions. Every suggested action
 * carries the §11 recommendation caveat via `ActionRecommendationCard` — a lead
 * is decision SUPPORT, never an instruction. Fed only by
 * `/intelligence/leads/{session}` (501 today → the panel degrades; no lead is
 * ever fabricated).
 */
import { Badge, Panel } from "@/design/primitives";
import { RiskBand } from "@/components/trust";
import type { IntelligenceLead } from "@/types/intelligence";

import { ActionRecommendationCard } from "./ActionRecommendationCard";
import { ConfidenceBadge } from "./ConfidenceBadge";

const PRIORITY_TONE: Record<IntelligenceLead["priority"], string | undefined> = {
  critical: "var(--risk-critical)",
  high: "var(--risk-high)",
  medium: "var(--risk-medium)",
  low: undefined,
};

interface LeadCardProps {
  lead: IntelligenceLead;
  onOpenEntity?: (kind: "case" | "person" | "location", id: string) => void;
}

export function LeadCard({ lead, onOpenEntity }: LeadCardProps) {
  return (
    <Panel className="flex flex-col gap-2 p-3">
      <div className="flex flex-wrap items-center gap-1.5">
        <Badge tone={PRIORITY_TONE[lead.priority]}>{lead.priority}</Badge>
        <ConfidenceBadge value={lead.confidence} />
        {lead.risk_band ? <RiskBand band={lead.risk_band} /> : null}
        <span className="ml-auto font-mono text-caption text-ink-faint">
          {lead.generated_at.slice(0, 10)}
        </span>
      </div>

      <p className="text-body text-ink-primary">{lead.headline}</p>
      <p className="text-caption text-ink-muted">{lead.reasoning}</p>

      {(lead.related_cases.length ||
        lead.related_persons.length ||
        lead.related_locations.length) > 0 ? (
        <div className="flex flex-wrap gap-1.5">
          {lead.related_cases.map((id) => (
            <RelatedChip key={`c-${id}`} label={`▣ ${id}`} onClick={() => onOpenEntity?.("case", id)} />
          ))}
          {lead.related_persons.map((id) => (
            <RelatedChip key={`p-${id}`} label={`◉ ${id}`} onClick={() => onOpenEntity?.("person", id)} />
          ))}
          {lead.related_locations.map((id) => (
            <RelatedChip key={`l-${id}`} label={`⬡ ${id}`} onClick={() => onOpenEntity?.("location", id)} />
          ))}
        </div>
      ) : null}

      {lead.suggested_actions.length ? (
        <div className="flex flex-col gap-1.5">
          {lead.suggested_actions.map((action, i) => (
            <ActionRecommendationCard key={i} action={action} />
          ))}
        </div>
      ) : null}
    </Panel>
  );
}

function RelatedChip({ label, onClick }: { label: string; onClick: () => void }) {
  return (
    <button
      type="button"
      onClick={onClick}
      className="rounded border border-line px-2 py-0.5 font-mono text-caption text-ink-muted hover:border-signal/40 hover:text-signal"
    >
      {label}
    </button>
  );
}
