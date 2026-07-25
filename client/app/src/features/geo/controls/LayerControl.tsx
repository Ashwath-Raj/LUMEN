/**
 * Floating layer control (§30.3 "floating layer control") — toggles the five
 * §30.3 layers. A layer whose backing data is unavailable is disabled with a
 * note (user brief: "Disable unavailable layers"), so the control never offers a
 * layer the map can't draw.
 */
import { Layers } from "lucide-react";

import { Panel } from "@/design/primitives";
import type { GeoLayer } from "@/types/geo";
import { cn } from "@/utils/cn";

interface LayerControlProps {
  active: GeoLayer[];
  /** Layers whose data is unavailable (disabled + noted). */
  unavailable: Set<GeoLayer>;
  onToggle: (layer: GeoLayer) => void;
}

const LAYER_LABEL: Record<GeoLayer, string> = {
  risk_choropleth: "Risk choropleth",
  incident_points: "Incident points",
  density: "Density (DBSCAN)",
  station_catchment: "Station catchment",
  reporting_delay: "Reporting delay",
};

const ORDER: GeoLayer[] = [
  "risk_choropleth",
  "incident_points",
  "density",
  "station_catchment",
  "reporting_delay",
];

export function LayerControl({
  active,
  unavailable,
  onToggle,
}: LayerControlProps) {
  return (
    <Panel elevated className="w-56 p-3">
      <h3 className="mb-2 flex items-center gap-1.5 text-caption uppercase tracking-wide text-ink-muted">
        <Layers size={14} strokeWidth={1.5} aria-hidden />
        Layers
      </h3>
      <ul className="flex flex-col gap-1">
        {ORDER.map((layer) => {
          const disabled = unavailable.has(layer);
          const checked = active.includes(layer);
          return (
            <li key={layer}>
              <label
                className={cn(
                  "flex items-center gap-2 text-caption",
                  disabled ? "cursor-not-allowed text-ink-faint" : "text-ink-muted",
                )}
              >
                <input
                  type="checkbox"
                  checked={checked && !disabled}
                  disabled={disabled}
                  onChange={() => onToggle(layer)}
                  className="accent-signal"
                />
                <span>{LAYER_LABEL[layer]}</span>
                {disabled ? (
                  <span className="ml-auto text-[10px] text-ink-faint">
                    unavailable
                  </span>
                ) : null}
              </label>
            </li>
          );
        })}
      </ul>
    </Panel>
  );
}
