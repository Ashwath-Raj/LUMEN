/**
 * `RelatedEntityCard` — a dense, selectable entity row for workbench side panels
 * and the Evidence Explorer. A thin composition over the D4 `EntityRef`
 * vocabulary (same glyphs, same inspector contract) tuned for list density —
 * NOT a second EntityCard implementation: selection still flows to the shared
 * InspectorPanel via the same `EntityRef`.
 */
import { ENTITY_GLYPH } from "@/design/tokens";
import type { EntityRef, EntityRefKind } from "@/components/entity";
import { cn } from "@/utils/cn";

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

interface RelatedEntityCardProps {
  entity: EntityRef;
  onSelect: (entity: EntityRef) => void;
  selected?: boolean;
  /** Extra affordance — add to investigation context. */
  onAddToContext?: (entity: EntityRef) => void;
  inContext?: boolean;
}

export function RelatedEntityCard({
  entity,
  onSelect,
  selected = false,
  onAddToContext,
  inContext = false,
}: RelatedEntityCardProps) {
  return (
    <div
      className={cn(
        "flex items-center gap-2 rounded border px-2 py-1.5",
        selected ? "border-signal/60 bg-raised" : "border-line hover:bg-raised",
      )}
    >
      <button
        type="button"
        onClick={() => onSelect(entity)}
        className="flex min-w-0 flex-1 items-center gap-2 text-left"
        aria-pressed={selected}
      >
        <span aria-hidden className="shrink-0 text-signal">
          {GLYPH[entity.kind]}
        </span>
        <span className="min-w-0 flex-1 truncate text-caption text-ink-primary">
          {entity.label}
        </span>
        {entity.sublabel ? (
          <span className="shrink-0 text-caption text-ink-faint">
            {entity.sublabel}
          </span>
        ) : null}
      </button>
      {onAddToContext ? (
        <button
          type="button"
          onClick={() => onAddToContext(entity)}
          aria-pressed={inContext}
          title={inContext ? "Remove from investigation context" : "Add to investigation context"}
          className={cn(
            "shrink-0 rounded border px-1.5 py-0.5 font-mono text-[10px]",
            inContext
              ? "border-signal/50 text-signal"
              : "border-line text-ink-faint hover:text-ink-primary",
          )}
        >
          {inContext ? "ctx ✓" : "+ctx"}
        </button>
      ) : null}
    </div>
  );
}
