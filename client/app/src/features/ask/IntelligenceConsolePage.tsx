/**
 * Intelligence Workbench — `/ask` (E.7, §30.7). The analyst
 * workstation: NOT a chatbot. Three dense panels + the shared Inspector:
 *
 *   LEFT    investigation context (case · persons · district scope · session
 *           timeline) — Part 5 memory, persisted in the URL
 *   CENTER  the AI intelligence session — AnalystQueryBox → REAL `POST /ai/ask`
 *           (orchestrator, §16.2; deterministic fallback §16.4) → answers as
 *           §8 Insights rendered as evidence-backed report cards
 *   RIGHT   Evidence Explorer (/persons + authentic districts) · §18
 *           recommendations · §13 anomalies · related cases
 *
 * Context retention: selections persist in the URL; each question is sent with
 * `district_scope` (the REAL request param) and the case/person context is
 * appended to the question text — shown transparently as chips, never hidden
 * prompt-engineering. Conversation content is session-local by design.
 */
import { useCallback, useMemo, useRef, useState } from "react";
import { useSearchParams } from "react-router-dom";

import { useAiAsk, useIntelligenceLeads, useActiveAlerts, usePersons } from "@/api";
import { ApiError } from "@/api";
import type { EntityRef } from "@/components/entity";
import {
  AnalystQueryBox,
  ConversationTimeline,
  InvestigationContextCard,
  LeadCard,
  sortLeads,
} from "@/components/intelligence";
import { InspectorPanel } from "@/components/inspector";
import { useInspector } from "@/hooks/useInspector";
import { useKarnatakaBoundaries } from "@/features/geo/useKarnatakaBoundaries";
import type { Evidence } from "@/types/contracts";
import type { Exchange, LeadSort } from "@/types/intelligence";
import { cn } from "@/utils/cn";

import { EvidenceExplorer } from "./EvidenceExplorer";
import {
  newSessionId,
  readWorkbenchContext,
  toggleId,
  writeWorkbenchContext,
} from "./workbenchUrlState";

const LEAD_SORTS: LeadSort[] = ["relevance", "priority", "confidence", "newest"];

export default function IntelligenceConsolePage() {
  const [params, setParams] = useSearchParams();
  const ctx = useMemo(() => readWorkbenchContext(params), [params]);

  // Establish a stable session id in the URL on first visit.
  const session = ctx.session || newSessionId();
  if (!ctx.session) {
    // One-time URL normalisation; replace so back doesn't bounce.
    setParams(writeWorkbenchContext(params, { session }), { replace: true });
  }

  const ask = useAiAsk();
  const leadsQuery = useIntelligenceLeads(session);
  const alertsQuery = useActiveAlerts();
  const personsQuery = usePersons();
  const boundaries = useKarnatakaBoundaries();

  const [exchanges, setExchanges] = useState<Exchange[]>([]);
  const [pinnedIds, setPinnedIds] = useState<Set<string>>(new Set());
  const [leadSort, setLeadSort] = useState<LeadSort>("relevance");

  const { selection, select, clear } = useInspector();
  const refCache = useRef<Map<string, EntityRef>>(new Map());

  // ── Context label resolution (persons via real list, districts via asset) ─
  const personItems = useMemo(
    () =>
      ctx.persons.map((id) => {
        const p = personsQuery.data?.persons.find((x) => x.person_id === id);
        return { id, label: p?.canonical_name ?? id, sublabel: p ? `${p.case_count}c` : undefined };
      }),
    [ctx.persons, personsQuery.data],
  );
  const districtItems = useMemo(
    () =>
      ctx.districts.map((id) => {
        const f = boundaries.data?.districts.features.find(
          (x) => x.properties.district_id === id,
        );
        return { id, label: f?.properties.district_name ?? id };
      }),
    [ctx.districts, boundaries.data],
  );

  const contextChips = useMemo(() => {
    const chips: string[] = [];
    if (ctx.caseId) chips.push(`case ${ctx.caseId}`);
    chips.push(...personItems.map((p) => p.label));
    chips.push(...districtItems.map((d) => d.label));
    return chips;
  }, [ctx.caseId, personItems, districtItems]);

  // ── Ask flow (REAL /ai/ask) ────────────────────────────────────────────
  const runAsk = useCallback(
    (question: string, exchangeId: string) => {
      // Compose the analyst's context INTO the question, transparently: the
      // real contract is {question, district_scope} — no session param exists,
      // so retention is client-side and visible as chips.
      const contextLine =
        ctx.caseId || ctx.persons.length
          ? ` (Investigation context: ${[
              ctx.caseId ? `case ${ctx.caseId}` : null,
              ...personItems.map((p) => `person ${p.label}`),
            ]
              .filter(Boolean)
              .join(", ")})`
          : "";
      const district_scope = ctx.districts
        .map((d) => Number.parseInt(d, 10))
        .filter((n) => Number.isFinite(n));

      ask.mutate(
        {
          question: question + contextLine,
          district_scope: district_scope.length ? district_scope : undefined,
        },
        {
          onSuccess: (insight) => {
            setExchanges((prev) =>
              prev.map((e) =>
                e.id === exchangeId ? { ...e, status: "answered", insight } : e,
              ),
            );
          },
          onError: (error) => {
            setExchanges((prev) =>
              prev.map((e) =>
                e.id === exchangeId
                  ? {
                      ...e,
                      status: "failed",
                      error:
                        error instanceof ApiError
                          ? error.message
                          : "The intelligence layer did not respond.",
                    }
                  : e,
              ),
            );
          },
        },
      );
    },
    [ask, ctx.caseId, ctx.persons.length, ctx.districts, personItems],
  );

  const onAsk = useCallback(
    (question: string) => {
      const id = newSessionId();
      const exchange: Exchange = {
        id,
        question,
        asked_at: new Date().toISOString(),
        scope_districts: districtItems.map((d) => d.label),
        status: "pending",
      };
      setExchanges((prev) => [...prev, exchange]);
      runAsk(question, id);
    },
    [districtItems, runAsk],
  );

  const onRetry = useCallback(
    (exchange: Exchange) => {
      setExchanges((prev) =>
        prev.map((e) =>
          e.id === exchange.id ? { ...e, status: "pending", error: undefined } : e,
        ),
      );
      runAsk(exchange.question, exchange.id);
    },
    [runAsk],
  );

  function onPin(id: string) {
    setPinnedIds((prev) => {
      const next = new Set(prev);
      if (next.has(id)) next.delete(id);
      else next.add(id);
      return next;
    });
  }

  // ── Inspector wiring ───────────────────────────────────────────────────
  const onSelectEntity = useCallback(
    (ref: EntityRef) => {
      refCache.current.set(`${ref.kind}:${ref.id}`, ref);
      select(ref);
    },
    [select],
  );
  const onEvidenceActivate = useCallback(
    (evidence: Evidence) => {
      onSelectEntity({
        kind: evidence.entity === "kb_document" ? "evidence" : "case",
        id: evidence.id,
        label: evidence.label,
        sublabel: evidence.entity,
        href: evidence.url,
      });
    },
    [onSelectEntity],
  );
  const selectedRef: EntityRef | null = useMemo(() => {
    if (!selection) return null;
    return (
      refCache.current.get(`${selection.kind}:${selection.id}`) ?? {
        kind: selection.kind,
        id: selection.id,
        label: selection.id,
      }
    );
  }, [selection]);

  // Session activity timeline (left panel).
  const activityTimeline = useMemo(
    () =>
      exchanges.map((e) => ({
        at: e.asked_at,
        label: `${pinnedIds.has(e.id) ? "📌 " : ""}${e.question}`,
      })),
    [exchanges, pinnedIds],
  );

  // Follow-up suggestions from the last answered subject.
  const followUps = useMemo(() => {
    const last = [...exchanges].reverse().find((e) => e.insight);
    if (!last?.insight) return [];
    const subject = `${last.insight.subject_type} ${last.insight.subject_id}`;
    return [
      `What evidence supports the last finding about ${subject}?`,
      `What are the limitations of the analysis on ${subject}?`,
      `Which related cases share entities with ${subject}?`,
    ];
  }, [exchanges]);

  const sortedLeads = useMemo(
    () =>
      leadsQuery.data
        ? sortLeads(leadsQuery.data, leadSort, {
            caseId: ctx.caseId,
            persons: ctx.persons,
            districts: ctx.districts,
          })
        : [],
    [leadsQuery.data, leadSort, ctx.caseId, ctx.persons, ctx.districts],
  );

  function patchCtx(patch: Parameters<typeof writeWorkbenchContext>[1]) {
    setParams(writeWorkbenchContext(params, patch));
  }

  return (
    <div className="relative isolate flex min-h-0 w-full flex-1 overflow-hidden">
      {/* ── LEFT · investigation context ─────────────────────────────────── */}
      <aside className="hidden w-72 shrink-0 flex-col gap-3 overflow-auto border-r border-line bg-panel p-3 lg:flex">
        <h1 className="font-display text-panel-title text-ink-primary">
          Intelligence Workbench
        </h1>
        <p className="font-mono text-caption text-ink-faint">
          session {session}
        </p>
        <InvestigationContextCard
          caseId={ctx.caseId}
          onClearCase={() => patchCtx({ caseId: null })}
          persons={personItems}
          onRemovePerson={(id) => patchCtx({ persons: ctx.persons.filter((p) => p !== id) })}
          districts={districtItems}
          onRemoveDistrict={(id) => patchCtx({ districts: ctx.districts.filter((d) => d !== id) })}
          timeline={activityTimeline}
        />
      </aside>

      {/* ── CENTER · AI session ──────────────────────────────────────────── */}
      <main className="flex min-w-0 flex-1 flex-col">
        <div className="min-h-0 flex-1 overflow-auto p-4">
          <ConversationTimeline
            exchanges={exchanges}
            pinnedIds={pinnedIds}
            onPin={onPin}
            onRetry={onRetry}
            onEvidenceActivate={onEvidenceActivate}
          />
        </div>
        <AnalystQueryBox
          onAsk={onAsk}
          busy={ask.isPending}
          contextChips={contextChips}
          followUps={followUps}
        />
      </main>

      {/* ── RIGHT · explorer + leads + alerts ────────────────────────────── */}
      <aside className="hidden w-80 shrink-0 flex-col gap-4 overflow-auto border-l border-line bg-panel p-3 xl:flex">
        <EvidenceExplorer
          onSelect={onSelectEntity}
          selectedId={selection?.id ?? null}
          onToggleContext={(kind, id) =>
            patchCtx(
              kind === "person"
                ? { persons: toggleId(ctx.persons, id) }
                : { districts: toggleId(ctx.districts, id) },
            )
          }
          contextPersons={ctx.persons}
          contextDistricts={ctx.districts}
        />

        <section aria-label="Suggested leads" className="flex flex-col gap-2">
          <div className="flex items-center gap-2">
            <h3 className="text-caption uppercase tracking-wide text-ink-muted">
              Suggested leads
            </h3>
            <div className="ml-auto flex gap-1">
              {LEAD_SORTS.map((s) => (
                <button
                  key={s}
                  type="button"
                  onClick={() => setLeadSort(s)}
                  aria-pressed={leadSort === s}
                  className={cn(
                    "rounded px-1.5 py-0.5 text-[10px] uppercase tracking-wide",
                    leadSort === s ? "bg-raised text-signal" : "text-ink-faint hover:text-ink-primary",
                  )}
                >
                  {s}
                </button>
              ))}
            </div>
          </div>
          {leadsQuery.isError || !sortedLeads.length ? (
            <p className="rounded border border-line px-3 py-3 text-caption text-ink-faint">
              {leadsQuery.isError
                ? "Lead generation isn’t available yet — the intelligence-leads service is not served. Leads appear here when it is."
                : "No leads for this session yet."}
            </p>
          ) : (
            sortedLeads.map((lead) => <LeadCard key={lead.lead_id} lead={lead} />)
          )}
        </section>

        <section aria-label="Active alerts" className="flex flex-col gap-2">
          <h3 className="text-caption uppercase tracking-wide text-ink-muted">
            Active alerts
          </h3>
          {alertsQuery.isError ? (
            <p className="rounded border border-line px-3 py-3 text-caption text-ink-faint">
              The alert feed is unavailable — anomaly alerts land here when the
              service is reachable.
            </p>
          ) : !alertsQuery.data?.length ? (
            <p className="rounded border border-line px-3 py-3 text-caption text-ink-faint">
              No active anomaly alerts in the current window.
            </p>
          ) : (
            <div className="flex flex-col gap-1.5">
              {alertsQuery.data.map((a) => (
                <div
                  key={a.id}
                  className="flex flex-col gap-0.5 rounded border border-degraded/40 px-3 py-2"
                >
                  <span className="text-caption text-ink-primary">{a.headline}</span>
                  <span className="font-mono text-[10px] text-ink-faint">
                    {a.subject_type} {a.subject_id} · {a.generated_at.slice(0, 10)}
                  </span>
                </div>
              ))}
            </div>
          )}
        </section>

        <section aria-label="Related cases" className="flex flex-col gap-2">
          <h3 className="text-caption uppercase tracking-wide text-ink-muted">
            Related cases · similar incidents
          </h3>
          <p className="rounded border border-line px-3 py-3 text-caption text-ink-faint">
            Case similarity isn’t available yet — the case service (
            <span className="font-mono">/investigation/cases</span>) is not
            implemented. Related cases surface here when it is.
          </p>
        </section>
      </aside>

      {/* Inspector overlay (shared, URL-synced). */}
      {selectedRef ? (
        <div className="absolute inset-y-0 right-0 z-inspector max-w-full">
          <InspectorPanel entity={selectedRef} onClose={clear} />
        </div>
      ) : null}
    </div>
  );
}
