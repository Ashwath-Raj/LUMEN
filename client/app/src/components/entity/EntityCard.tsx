/**
 * `EntityCard` (D4) — one semantic entity, compact or full (§2.1/§2.3). Renders
 * the fixed entity glyph (§F), the §2.3 label, an optional sublabel, and — in
 * full — a fields grid plus an "Open full view" drill-in. Used for workspace
 * entities, the dossier, lists, and the inspector (arch D4).
 *
 * Governance is visible: a classification badge renders when present, and a
 * masked entity shows the lock affordance, never blank space (§4.2, §31.2).
 * No layout assumptions are hardcoded — the card is width-fluid.
 */
import { Link } from "react-router-dom";
import { ArrowUpRight, Lock } from "lucide-react";

import { Panel } from "@/design/primitives";
import { ClassificationBadge } from "@/components/trust";
import { ENTITY_GLYPH } from "@/design/tokens";
import { cn } from "@/utils/cn";
import type { EntityRef, EntityRefKind } from "./entityRef";

interface EntityCardProps {
  entity: EntityRef;
  variant?: "compact" | "full";
  /** Select this entity (e.g. into the InspectorPanel) instead of navigating. */
  onSelect?: (entity: EntityRef) => void;
  selected?: boolean;
  className?: string;
}

/** Glyph per ref kind — shared entity types keep the global §F glyph. */
const GLYPH: Record<EntityRefKind, string> = {
  case: ENTITY_GLYPH.case,
  person: ENTITY_GLYPH.person,
  officer: ENTITY_GLYPH.officer,
  station: ENTITY_GLYPH.station,
  location: ENTITY_GLYPH.district,
  charge: ENTITY_GLYPH.charge,
  evidence: "❏",
  insight: ENTITY_GLYPH.insight,
};

export function EntityCard({
  entity,
  variant = "compact",
  onSelect,
  selected = false,
  className,
}: EntityCardProps) {
  const full = variant === "full";

  const head = (
    <div className="flex min-w-0 items-start gap-2">
      <span aria-hidden className="mt-0.5 text-signal">
        {GLYPH[entity.kind]}
      </span>
      <div className="flex min-w-0 flex-col">
        <span className="flex items-center gap-1.5 truncate text-body text-ink-primary">
          {entity.masked ? (
            <Lock size={12} strokeWidth={1.5} className="text-ink-faint" aria-hidden />
          ) : null}
          {entity.label}
        </span>
        {entity.sublabel ? (
          <span className="truncate text-caption text-ink-muted">
            {entity.sublabel}
          </span>
        ) : null}
      </div>
      {entity.classification ? (
        <span className="ml-auto">
          <ClassificationBadge classification={entity.classification} />
        </span>
      ) : null}
    </div>
  );

  const body = (
    <Panel
      className={cn(
        "flex flex-col gap-2 p-3",
        onSelect && "cursor-pointer hover:border-signal/40",
        selected && "border-signal/60",
        className,
      )}
    >
      {head}

      {full && entity.fields?.length ? (
        <dl className="grid grid-cols-[auto_1fr] gap-x-4 gap-y-1 text-caption">
          {entity.fields.map((field) => (
            <div key={field.label} className="contents">
              <dt className="text-ink-faint">{field.label}</dt>
              <dd className={cn("text-ink-muted", field.mono && "font-mono")}>
                {field.value}
              </dd>
            </div>
          ))}
        </dl>
      ) : null}

      {full && entity.href ? (
        <Link
          to={entity.href}
          className="inline-flex items-center gap-1 text-caption text-signal hover:underline"
        >
          Open full view
          <ArrowUpRight size={12} aria-hidden />
        </Link>
      ) : null}
    </Panel>
  );

  if (onSelect) {
    return (
      <button
        type="button"
        onClick={() => onSelect(entity)}
        aria-pressed={selected}
        className="w-full text-left"
      >
        {body}
      </button>
    );
  }

  return body;
}
