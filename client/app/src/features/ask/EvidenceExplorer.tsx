/**
 * Evidence Explorer (Part 4) — browse investigable entities by type; each opens
 * the shared Inspector and can be added to the investigation context.
 *
 * Honest sourcing per type:
 *   Persons    → REAL `GET /persons` (resolved identities, live data)
 *   Locations  → the 30 authentic Karnataka districts (static reference
 *                geometry — legitimate, non-crime data; they also drive the
 *                REAL `/ai/ask` district_scope)
 *   Documents · Vehicles · Organizations · Phones · Evidence
 *              → NO backend endpoint exposes these registries; each tab states
 *                that explicitly. Nothing is fabricated.
 */
import { useMemo, useState } from "react";

import { usePersons } from "@/api";
import { RelatedEntityCard } from "@/components/intelligence";
import { QueryBoundary } from "@/components/states";
import type { EntityRef } from "@/components/entity";
import { useKarnatakaBoundaries } from "@/features/geo/useKarnatakaBoundaries";
import { cn } from "@/utils/cn";

type ExplorerTab =
  | "persons"
  | "locations"
  | "documents"
  | "vehicles"
  | "organizations"
  | "phones"
  | "evidence";

const TABS: Array<{ id: ExplorerTab; label: string }> = [
  { id: "persons", label: "Persons" },
  { id: "locations", label: "Locations" },
  { id: "documents", label: "Documents" },
  { id: "vehicles", label: "Vehicles" },
  { id: "organizations", label: "Orgs" },
  { id: "phones", label: "Phones" },
  { id: "evidence", label: "Evidence" },
];

/** Registries with no backing endpoint in the OpenAPI. */
const UNAVAILABLE_NOTE: Partial<Record<ExplorerTab, string>> = {
  documents: "No document registry endpoint exists yet. Documents cited by AI answers appear as evidence chips on the answer itself.",
  vehicles: "No vehicle registry endpoint exists yet. Vehicles will list here when the backend exposes them.",
  organizations: "No organization registry endpoint exists yet.",
  phones: "No phone-number registry endpoint exists yet.",
  evidence: "No standalone evidence registry endpoint exists yet. Evidence is cited per answer and per insight.",
};

interface EvidenceExplorerProps {
  onSelect: (ref: EntityRef) => void;
  selectedId: string | null;
  onToggleContext: (kind: "person" | "district", id: string) => void;
  contextPersons: string[];
  contextDistricts: string[];
}

export function EvidenceExplorer({
  onSelect,
  selectedId,
  onToggleContext,
  contextPersons,
  contextDistricts,
}: EvidenceExplorerProps) {
  const [tab, setTab] = useState<ExplorerTab>("persons");
  const personsQuery = usePersons();
  const boundaries = useKarnatakaBoundaries();

  const districtRefs = useMemo<EntityRef[]>(() => {
    const features = boundaries.data?.districts.features ?? [];
    return [...features]
      .sort((a, b) =>
        a.properties.district_name.localeCompare(b.properties.district_name),
      )
      .map((f) => ({
        kind: "location" as const,
        id: f.properties.district_id,
        label: f.properties.district_name,
        sublabel: `LGD ${f.properties.lgd}`,
        href: `/geo?district=${f.properties.district_id}`,
        fields: [
          { label: "census code", value: f.properties.district_id, mono: true },
          { label: "LGD code", value: String(f.properties.lgd), mono: true },
        ],
      }));
  }, [boundaries.data]);

  return (
    <section aria-label="Evidence explorer" className="flex min-h-0 flex-col gap-2">
      <div className="flex flex-wrap gap-1" role="tablist" aria-label="Entity types">
        {TABS.map((t) => (
          <button
            key={t.id}
            role="tab"
            aria-selected={tab === t.id}
            onClick={() => setTab(t.id)}
            className={cn(
              "rounded border px-2 py-0.5 text-caption transition-colors duration-DEFAULT ease-ease",
              tab === t.id
                ? "border-signal/50 text-signal"
                : "border-line text-ink-muted hover:text-ink-primary",
            )}
          >
            {t.label}
          </button>
        ))}
      </div>

      <div className="min-h-0 flex-1 overflow-auto">
        {tab === "persons" ? (
          <QueryBoundary
            query={personsQuery}
            emptyMessage="No resolved identities yet — entity resolution has not produced any persons."
            degradedMessage="The identity service is unavailable."
            isEmpty={(d) => d.persons.length === 0}
            skeletonLines={5}
          >
            {(data) => (
              <div className="flex flex-col gap-1">
                {data.persons.map((p) => (
                  <RelatedEntityCard
                    key={p.person_id}
                    entity={{
                      kind: "person",
                      id: p.person_id,
                      label: p.canonical_name,
                      sublabel: `${p.case_count}c · ${p.resolution_confidence.toFixed(2)}`,
                      href: `/person/${p.person_id}`,
                      fields: [
                        { label: "about", value: p.description },
                        { label: "districts", value: String(p.district_count) },
                        { label: "confidence", value: p.resolution_confidence.toFixed(2), mono: true },
                      ],
                    }}
                    onSelect={onSelect}
                    selected={selectedId === p.person_id}
                    onAddToContext={(ref) => onToggleContext("person", ref.id)}
                    inContext={contextPersons.includes(p.person_id)}
                  />
                ))}
              </div>
            )}
          </QueryBoundary>
        ) : tab === "locations" ? (
          <div className="flex flex-col gap-1">
            {districtRefs.map((ref) => (
              <RelatedEntityCard
                key={ref.id}
                entity={ref}
                onSelect={onSelect}
                selected={selectedId === ref.id}
                onAddToContext={(r) => onToggleContext("district", r.id)}
                inContext={contextDistricts.includes(ref.id)}
              />
            ))}
          </div>
        ) : (
          <p className="rounded border border-line px-3 py-4 text-caption text-ink-faint">
            {UNAVAILABLE_NOTE[tab]}
          </p>
        )}
      </div>
    </section>
  );
}
