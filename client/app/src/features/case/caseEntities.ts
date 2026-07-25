/**
 * Map a `CaseDetail` to `EntityRef`s for the Overview tab + InspectorPanel
 * (feature assembly, arch §G). This is where the case's typed fields become the
 * normalized entity descriptors the reusable `EntityCard`/`InspectorPanel`
 * render — so the components stay decoupled from the case shape.
 *
 * P9/§4.2 is respected upstream: the API returns masked participant names
 * (`masked: true`), which flow straight onto the ref; caste/religion/DOB are
 * never present on `CaseDetail`, so they cannot leak here.
 */
import type { EntityRef } from "@/components/entity";
import type { CaseDetail } from "@/types/case";

export function officerRefs(detail: CaseDetail): EntityRef[] {
  return detail.officers.map((o) => ({
    kind: "officer",
    id: o.employee_id,
    label: o.display_name,
    sublabel: [o.rank_short_name, o.station_name].filter(Boolean).join(" · ") || undefined,
    fields: [
      { label: "role", value: o.role === "investigating" ? "Investigating officer" : "Registering officer" },
      { label: "rank", value: o.rank_short_name ?? "—" },
      { label: "station", value: o.station_name ?? "—" },
      { label: "employee id", value: o.employee_id, mono: true },
    ],
    href: `/cases?officer=${o.employee_id}`,
  }));
}

export function participantRefs(detail: CaseDetail): EntityRef[] {
  return detail.participants.map((p) => ({
    kind: "person",
    id: p.person_id ?? `${p.role}:${p.label}`,
    label: `${p.label} · ${p.display_name}`,
    sublabel: p.role,
    masked: p.masked,
    fields: [
      { label: "role", value: p.role },
      { label: "label", value: p.label, mono: true },
      { label: "resolved", value: p.person_id ? "yes" : "not resolved" },
    ],
    // Only resolved persons drill into a dossier (§6); unresolved stay in-panel.
    href: p.person_id ? `/person/${p.person_id}` : null,
    classification: "RESTRICTED",
  }));
}

export function stationRef(detail: CaseDetail): EntityRef {
  return {
    kind: "station",
    id: detail.station.unit_id,
    label: detail.station.unit_name,
    sublabel: detail.station.district_name,
    fields: [
      { label: "district", value: detail.station.district_name },
      { label: "unit id", value: detail.station.unit_id, mono: true },
    ],
    href: `/cases?station=${detail.station.unit_id}`,
  };
}

export function chargeRefs(detail: CaseDetail): EntityRef[] {
  return detail.charges.map((c, i) => ({
    kind: "charge",
    id: `${c.act_short_name}-${c.section_id}-${i}`,
    label: `${c.act_short_name} ${c.section_id}`,
    sublabel: c.section_description ?? undefined,
    fields: [
      { label: "act", value: c.act_short_name },
      { label: "section", value: c.section_id, mono: true },
      { label: "description", value: c.section_description ?? "—" },
    ],
  }));
}
