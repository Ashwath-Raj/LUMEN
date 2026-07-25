/**
 * `EntityRef` — a normalized descriptor for one selectable entity, the decoupled
 * contract between a surface that HAS entities (the Case Workspace) and the
 * components that DISPLAY one (`EntityCard`, `InspectorPanel`). The workspace
 * builds an `EntityRef` from its typed data; the inspector renders it without
 * knowing where it came from. This is why the inspector can show a person, a
 * location, an officer, evidence, an insight or a case with one component (D10).
 *
 * The `kind` is the §2.1 entity vocabulary (plus "location"/"evidence" for the
 * two inspector targets that aren't bare entities). `fields` are label→value
 * pairs rendered as-is; `href` (when set) is the "open full view" drill-in.
 */
export type EntityRefKind =
  | "case"
  | "person"
  | "officer"
  | "station"
  | "location"
  | "charge"
  | "evidence"
  | "insight";

export interface EntityField {
  label: string;
  value: string;
  /** Render the value in mono (identifiers, §F). */
  mono?: boolean;
}

export interface EntityRef {
  kind: EntityRefKind;
  /** Stable id used for URL selection state (`?inspect=kind:id`). */
  id: string;
  /** Primary display label (the §2.3 render form where one exists). */
  label: string;
  /** Optional secondary line (e.g. role, status). */
  sublabel?: string;
  /** Detail fields shown in the full/inspector view. */
  fields?: EntityField[];
  /** Drill-in target for "open full view"; null keeps focus in the workspace. */
  href?: string | null;
  /** Governance class, if the entity carries one (§4.1). */
  classification?: "PUBLIC" | "INTERNAL" | "CONFIDENTIAL" | "RESTRICTED";
  /** Masked per role below threshold (§4.2). */
  masked?: boolean;
}

/** Serialize/parse the URL selection token `kind:id`. */
export function encodeEntityRef(ref: Pick<EntityRef, "kind" | "id">): string {
  return `${ref.kind}:${ref.id}`;
}

export function parseEntityRefToken(
  token: string,
): { kind: EntityRefKind; id: string } | null {
  const idx = token.indexOf(":");
  if (idx === -1) return null;
  const kind = token.slice(0, idx) as EntityRefKind;
  const id = token.slice(idx + 1);
  if (!id) return null;
  return { kind, id };
}
