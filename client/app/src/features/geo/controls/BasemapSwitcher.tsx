/**
 * Basemap switcher (user brief "Multiple basemaps") — dark intelligence /
 * standard / satellite. A small segmented control; the dark map is the
 * command-center default.
 */
import { Panel } from "@/design/primitives";
import { BASEMAPS, type BasemapId } from "../basemaps";
import { cn } from "@/utils/cn";

interface BasemapSwitcherProps {
  active: BasemapId;
  onChange: (id: BasemapId) => void;
}

const ORDER: BasemapId[] = ["dark", "standard", "satellite"];

export function BasemapSwitcher({ active, onChange }: BasemapSwitcherProps) {
  return (
    <Panel elevated className="flex items-center gap-1 p-1">
      {ORDER.map((id) => (
        <button
          key={id}
          type="button"
          onClick={() => onChange(id)}
          aria-pressed={active === id}
          className={cn(
            "rounded px-2 py-1 text-caption transition-colors duration-DEFAULT ease-ease",
            active === id
              ? "bg-raised text-signal"
              : "text-ink-muted hover:text-ink-primary",
          )}
        >
          {BASEMAPS[id].label}
        </button>
      ))}
    </Panel>
  );
}
