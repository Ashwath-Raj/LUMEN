/**
 * `ConversationTimeline` — the session's exchanges as a chronological
 * intelligence log (newest last, pinned first in their own group). Session-local
 * by design: the spec audits AI queries server-side but defines no user-facing
 * history store (arch §D "the Console history rail is session-local"), so
 * nothing pretends to persist.
 */
import { EmptyState } from "@/design/primitives";
import type { Evidence } from "@/types/contracts";
import type { Exchange } from "@/types/intelligence";

import { IntelligenceCard } from "./IntelligenceCard";

interface ConversationTimelineProps {
  exchanges: Exchange[];
  pinnedIds: Set<string>;
  onPin: (id: string) => void;
  onRetry: (exchange: Exchange) => void;
  onEvidenceActivate?: (evidence: Evidence) => void;
}

export function ConversationTimeline({
  exchanges,
  pinnedIds,
  onPin,
  onRetry,
  onEvidenceActivate,
}: ConversationTimelineProps) {
  if (exchanges.length === 0) {
    return (
      <EmptyState message="No analysis yet this session. Ask a question below — answers are grounded in canonical records and arrive as evidence-backed intelligence, never as unsourced claims." />
    );
  }

  const pinned = exchanges.filter((e) => pinnedIds.has(e.id));
  const rest = exchanges.filter((e) => !pinnedIds.has(e.id));

  return (
    <div className="flex flex-col gap-3">
      {pinned.length ? (
        <section aria-label="Pinned analysis" className="flex flex-col gap-2">
          <h3 className="text-caption uppercase tracking-wide text-signal">
            Pinned ({pinned.length})
          </h3>
          {pinned.map((exchange) => (
            <IntelligenceCard
              key={exchange.id}
              exchange={exchange}
              pinned
              onPin={onPin}
              onRetry={onRetry}
              onEvidenceActivate={onEvidenceActivate}
            />
          ))}
        </section>
      ) : null}

      {rest.map((exchange) => (
        <IntelligenceCard
          key={exchange.id}
          exchange={exchange}
          pinned={false}
          onPin={onPin}
          onRetry={onRetry}
          onEvidenceActivate={onEvidenceActivate}
        />
      ))}
    </div>
  );
}
