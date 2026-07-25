/**
 * Person Dossier — `/person/:id` (E.5, §6.4, §30.5). An intelligence profile of
 * a resolved, uncertain identity — never a CRUD person page. IdentityBanner
 * first, always (§30.5), then linked case records, associates ranked by shared
 * cases, the ego graph, and candidate matches (<0.85) in a clearly separated
 * block (§6.4), excluded from the metrics above.
 *
 * This surface consumes the REAL, DB-backed `GET /persons/{id}` — the one
 * Session-4 surface with genuine live data. The ego graph (`/persons/{id}/network`)
 * has no backend endpoint yet, so it degrades gracefully. Node/dispute actions
 * open the Inspector without leaving the dossier.
 */
import { useMemo, useRef } from "react";
import { useParams } from "react-router-dom";

import { usePerson, usePersonNetwork } from "@/api";
import { GraphSurface } from "@/components/graph";
import { IdentityBanner } from "@/components/person";
import { InspectorPanel } from "@/components/inspector";
import { QueryBoundary } from "@/components/states";
import type { EntityRef } from "@/components/entity";
import { Panel } from "@/design/primitives";
import { CONFIDENCE_TOKEN, confidenceBand } from "@/design/tokens";
import { useInspector } from "@/hooks/useInspector";
import type { PersonLink } from "@/types/person";

export default function PersonDossierPage() {
  const { id = "" } = useParams();
  const personQuery = usePerson(id);
  const egoQuery = usePersonNetwork(id);
  const { selection, select, clear } = useInspector();
  const refCache = useRef<Map<string, EntityRef>>(new Map());

  function onSelectEntity(ref: EntityRef) {
    refCache.current.set(`${ref.kind}:${ref.id}`, ref);
    select(ref);
  }

  const selectedRef: EntityRef | null = useMemo(() => {
    if (!selection) return null;
    const token = `${selection.kind}:${selection.id}`;
    return (
      refCache.current.get(token) ?? {
        kind: selection.kind,
        id: selection.id,
        label: selection.id,
      }
    );
  }, [selection]);

  return (
    <div className="relative flex min-h-0 w-full flex-1">
      <div className="min-h-0 flex-1 overflow-auto p-6">
        <QueryBoundary
          query={personQuery}
          emptyMessage="No dossier for this identity."
          degradedMessage="The identity service isn’t available. This dossier will populate once /persons is reachable."
          skeletonLines={8}
        >
          {(person) => (
            <div className="mx-auto flex max-w-5xl flex-col gap-6">
              <IdentityBanner person={person} />

              <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
                {/* Linked case records (auto-linked, §6.4) */}
                <section className="flex flex-col gap-2">
                  <h3 className="text-caption uppercase tracking-wide text-ink-muted">
                    Linked records ({person.linked.length})
                  </h3>
                  {person.linked.length ? (
                    <div className="flex flex-col gap-2">
                      {person.linked.map((link) => (
                        <LinkRow key={link.accused_master_id} link={link} />
                      ))}
                    </div>
                  ) : (
                    <p className="text-caption text-ink-faint">
                      No auto-linked records.
                    </p>
                  )}
                </section>

                {/* Ego graph (degraded — no endpoint) */}
                <section className="flex min-h-[320px] flex-col gap-2">
                  <h3 className="text-caption uppercase tracking-wide text-ink-muted">
                    Ego network
                  </h3>
                  <Panel className="relative min-h-0 flex-1 overflow-hidden">
                    <GraphSurface
                      payload={egoQuery.data}
                      isLoading={egoQuery.isLoading}
                      error={egoQuery.error}
                      onSelect={onSelectEntity}
                      degradedMessage="Live ego-graph intelligence is unavailable. No relationships are shown."
                      emptyMessage="No network connections resolved for this identity."
                    />
                  </Panel>
                </section>
              </div>

              {/* Candidate matches — separated, excluded from metrics (§6.4) */}
              {person.candidates.length ? (
                <section className="flex flex-col gap-2">
                  <h3 className="text-caption uppercase tracking-wide text-ink-muted">
                    Candidate matches (below threshold) — {person.candidates.length}
                  </h3>
                  <p className="text-caption text-ink-faint">
                    Shown separately and excluded from the metrics above; these are
                    possible, not confirmed, links (§6.4).
                  </p>
                  <div className="flex flex-col gap-2">
                    {person.candidates.map((link) => (
                      <LinkRow key={link.accused_master_id} link={link} candidate />
                    ))}
                  </div>
                </section>
              ) : null}
            </div>
          )}
        </QueryBoundary>
      </div>

      {selectedRef ? (
        <div className="absolute inset-y-0 right-0 z-inspector max-w-full xl:static">
          <InspectorPanel entity={selectedRef} onClose={clear} />
        </div>
      ) : null}
    </div>
  );
}

function LinkRow({ link, candidate = false }: { link: PersonLink; candidate?: boolean }) {
  const band = confidenceBand(link.confidence);
  return (
    <Panel className="flex items-center gap-3 p-3">
      <span className="font-mono text-caption text-ink-muted">
        accused #{link.accused_master_id}
      </span>
      <span
        className="ml-auto font-mono text-caption"
        style={{ color: CONFIDENCE_TOKEN[band] }}
        title="Match confidence"
      >
        {link.confidence.toFixed(2)}
      </span>
      {candidate ? (
        <span className="rounded border border-line px-2 py-0.5 text-caption text-ink-faint">
          candidate
        </span>
      ) : null}
    </Panel>
  );
}
