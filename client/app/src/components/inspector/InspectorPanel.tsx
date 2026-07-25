/**
 * `InspectorPanel` (D10) — the persistent right panel that shows details for
 * whichever entity is selected, WITHOUT navigating away from the workspace
 * (arch D10; Session 2 prompt "The Inspector Panel must remain persistent…
 * No navigation away from workspace"). Docked mode (380px, §F) for the Case
 * Workspace; the overlay mode (map/list peeks) is a later session.
 *
 * Content is an `EntityRef` (D4 `EntityCard` full) for person/location/officer/
 * evidence/case, and an `InsightCard` for an insight — one component, six entity
 * types (Session 2 prompt). When nothing is selected it shows an instructional
 * empty state, never a blank panel.
 *
 * A11y: labelled complementary region; Esc clears the selection; the close
 * button is reachable and labelled. Selection lives in the URL (`useInspector`),
 * so the panel is shareable and survives refresh.
 */
import { useEffect } from "react";
import { X } from "lucide-react";

import { EmptyState } from "@/design/primitives";
import { EntityCard, type EntityRef } from "@/components/entity";
import { InsightCard } from "@/components/insight";
import type { Insight } from "@/types/contracts";

interface InspectorPanelProps {
  /** The resolved entity to show, or null when nothing is selected. */
  entity: EntityRef | null;
  /** When the selected entity is an insight, its full object for the InsightCard. */
  insight?: Insight | null;
  onClose: () => void;
}

const KIND_TITLE: Record<EntityRef["kind"], string> = {
  case: "Case",
  person: "Person",
  officer: "Officer",
  station: "Station",
  location: "Location",
  charge: "Charge",
  evidence: "Evidence",
  insight: "Insight",
};

export function InspectorPanel({
  entity,
  insight,
  onClose,
}: InspectorPanelProps) {
  useEffect(() => {
    if (!entity) return;
    function onKey(e: KeyboardEvent) {
      if (e.key === "Escape") onClose();
    }
    document.addEventListener("keydown", onKey);
    return () => document.removeEventListener("keydown", onKey);
  }, [entity, onClose]);

  return (
    <aside
      aria-label="Inspector"
      className="flex h-full flex-col border-l border-line bg-panel"
      style={{ width: "var(--inspector-docked)" }}
    >
      <div className="flex items-center gap-2 border-b border-line px-4 py-3">
        <h2 className="text-caption uppercase tracking-wide text-ink-muted">
          {entity ? KIND_TITLE[entity.kind] : "Inspector"}
        </h2>
        {entity ? (
          <button
            type="button"
            onClick={onClose}
            aria-label="Close inspector"
            className="ml-auto text-ink-faint hover:text-ink-primary"
          >
            <X size={16} />
          </button>
        ) : null}
      </div>

      <div className="min-h-0 flex-1 overflow-auto p-4">
        {!entity ? (
          <EmptyState message="Select a person, location, officer, evidence item or insight to inspect it here — without leaving the case." />
        ) : entity.kind === "insight" && insight ? (
          <InsightCard insight={insight} variant="expanded" />
        ) : (
          <EntityCard entity={entity} variant="full" />
        )}
      </div>
    </aside>
  );
}
