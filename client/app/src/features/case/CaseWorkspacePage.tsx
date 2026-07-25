/**
 * Case Workspace — `/case/:id` (E.4). The hero surface: everything about one FIR
 * on one screen, hours of work without leaving. This is an analyst workspace, not
 * a dashboard.
 *
 * Layout (Session 2 prompt): Header → Summary Strip → Main Workspace (tabbed:
 * Overview · Timeline · Insights · Evidence · Activity) → persistent Inspector
 * Panel. The active tab and the inspector selection both live in the URL (§C),
 * so the whole view is shareable and survives refresh, and browser-back works
 * mid-investigation.
 *
 * Graph / Geo / Forecasts are explicitly NOT here (later sessions). Feature
 * assembly only — every reusable part comes from `components/` and `design/`.
 */
import { useMemo } from "react";
import { useParams, useSearchParams } from "react-router-dom";

import { useCase, useCaseInsights } from "@/api";
import { InspectorPanel } from "@/components/inspector";
import { QueryBoundary } from "@/components/states";
import type { EntityRef } from "@/components/entity";
import { Tabs, type TabItem } from "@/design/primitives";
import { useInspector } from "@/hooks/useInspector";
import type { CaseDetail } from "@/types/case";
import type { Insight } from "@/types/contracts";
import { writeParams } from "@/utils/urlState";

import { CaseHeader } from "./CaseHeader";
import { CaseSummaryStrip } from "./CaseSummaryStrip";
import {
  chargeRefs,
  officerRefs,
  participantRefs,
  stationRef,
} from "./caseEntities";
import { ActivityTab } from "./tabs/ActivityTab";
import { EvidenceTab } from "./tabs/EvidenceTab";
import { InsightsTab } from "./tabs/InsightsTab";
import { OverviewTab } from "./tabs/OverviewTab";
import { TimelineTab } from "./tabs/TimelineTab";

const TABS: TabItem[] = [
  { id: "overview", label: "Overview" },
  { id: "timeline", label: "Timeline" },
  { id: "insights", label: "Insights" },
  { id: "evidence", label: "Evidence" },
  { id: "activity", label: "Activity" },
];

const DEFAULT_TAB = "overview";

export default function CaseWorkspacePage() {
  const { id = "" } = useParams();
  const [params, setParams] = useSearchParams();

  const caseQuery = useCase(id);
  // Insights are also needed to resolve an inspector selection of kind "insight".
  const insightsQuery = useCaseInsights(id);

  const { selection, select, clear } = useInspector();

  const activeTab = params.get("tab") ?? DEFAULT_TAB;
  function setTab(tab: string) {
    setParams(writeParams(params, { tab: tab === DEFAULT_TAB ? null : tab }));
  }

  // Resolve the URL selection token to a concrete EntityRef from loaded data,
  // so the inspector needs no extra fetch for entities the workspace holds.
  const resolved = useMemo<{ ref: EntityRef | null; insight: Insight | null }>(() => {
    if (!selection) return { ref: null, insight: null };

    if (selection.kind === "insight") {
      const insight =
        insightsQuery.data?.find((i) => i.id === selection.id) ?? null;
      return {
        ref: insight
          ? { kind: "insight", id: insight.id, label: insight.headline }
          : null,
        insight,
      };
    }

    const detail = caseQuery.data;
    if (!detail) return { ref: null, insight: null };
    const ref =
      resolveRefs(detail).find(
        (r) => r.kind === selection.kind && r.id === selection.id,
      ) ?? null;
    return { ref, insight: null };
  }, [selection, caseQuery.data, insightsQuery.data]);

  const selectedId = resolved.ref?.id ?? null;

  return (
    <div className="flex h-full min-h-0">
      <div className="flex min-w-0 flex-1 flex-col">
        <QueryBoundary
          query={caseQuery}
          emptyMessage="This case has no detail to show."
          skeletonLines={8}
        >
          {(detail) => (
            <>
              <CaseHeader detail={detail} />
              <CaseSummaryStrip detail={detail} onGoToTab={setTab} />
              <div className="px-6">
                <Tabs
                  tabs={TABS}
                  activeId={activeTab}
                  onChange={setTab}
                  idBase="case"
                />
              </div>
              <div
                id={`case-panel-${activeTab}`}
                role="tabpanel"
                aria-labelledby={`case-${activeTab}`}
                className="min-h-0 flex-1 overflow-auto p-6"
              >
                {activeTab === "timeline" ? (
                  <TimelineTab caseId={id} />
                ) : activeTab === "insights" ? (
                  <InsightsTab caseId={id} onSelectInsight={(ref) => select(ref)} />
                ) : activeTab === "evidence" ? (
                  <EvidenceTab caseId={id} />
                ) : activeTab === "activity" ? (
                  <ActivityTab caseId={id} />
                ) : (
                  <OverviewTab
                    detail={detail}
                    onSelect={select}
                    selectedId={selectedId}
                  />
                )}
              </div>
            </>
          )}
        </QueryBoundary>
      </div>

      {/* Inspector: docked inline ≥1280 (§F three-column). Below that the right
          column collapses — it renders as a right overlay only when an entity is
          selected (§F "below 1280 the right column collapses into inspector-
          toggles"), so the tab content keeps full width. */}
      <div
        className={
          resolved.ref
            ? "fixed inset-y-0 right-0 z-inspector shadow-panel xl:static xl:z-auto xl:shadow-none"
            : "hidden xl:block"
        }
      >
        <InspectorPanel
          entity={resolved.ref}
          insight={resolved.insight}
          onClose={clear}
        />
      </div>
    </div>
  );
}

/** All inspector-selectable refs derivable from the loaded case detail. */
function resolveRefs(detail: CaseDetail): EntityRef[] {
  return [
    ...officerRefs(detail),
    ...participantRefs(detail),
    ...chargeRefs(detail),
    stationRef(detail),
  ];
}
