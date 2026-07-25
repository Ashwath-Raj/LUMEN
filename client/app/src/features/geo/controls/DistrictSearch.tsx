/**
 * District search/jump (Session-3 "Search integration") — a type-ahead over the
 * 30 authentic Karnataka districts that drills the map to the chosen district
 * (centres + selects it). This is search integrated INTO the map surface; it
 * needs no backend (the district list is the static boundary data), so it works
 * even while `/geo/*` is degraded. Complements the shell's global ⌘K search.
 */
import { useMemo, useState } from "react";
import { Search, X } from "lucide-react";
import type { Feature, MultiPolygon, Polygon } from "geojson";

import { Panel } from "@/design/primitives";
import type { DistrictFeatureProps } from "../data/karnataka";
import type { DistrictCollection } from "../useKarnatakaBoundaries";
import { cn } from "@/utils/cn";

interface DistrictSearchProps {
  districts: DistrictCollection | undefined;
  onPick: (districtId: string, center: [number, number]) => void;
}

/** Approximate centroid (bbox centre) of a district polygon, as [lat, lng]. */
function centroidOf(
  feature: Feature<Polygon | MultiPolygon, DistrictFeatureProps>,
): [number, number] {
  let minLat = 90,
    maxLat = -90,
    minLng = 180,
    maxLng = -180;
  const visit = (a: unknown): void => {
    if (
      Array.isArray(a) &&
      typeof a[0] === "number" &&
      typeof a[1] === "number"
    ) {
      const [lng, lat] = a as number[];
      minLat = Math.min(minLat, lat);
      maxLat = Math.max(maxLat, lat);
      minLng = Math.min(minLng, lng);
      maxLng = Math.max(maxLng, lng);
    } else if (Array.isArray(a)) {
      a.forEach(visit);
    }
  };
  visit(feature.geometry.coordinates);
  return [(minLat + maxLat) / 2, (minLng + maxLng) / 2];
}

export function DistrictSearch({ districts, onPick }: DistrictSearchProps) {
  const [q, setQ] = useState("");
  const [open, setOpen] = useState(false);

  const matches = useMemo(() => {
    const features = districts?.features ?? [];
    const query = q.trim().toLowerCase();
    const list = query
      ? features.filter((f) =>
          f.properties.district_name.toLowerCase().includes(query),
        )
      : features;
    return [...list]
      .sort((a, b) =>
        a.properties.district_name.localeCompare(b.properties.district_name),
      )
      .slice(0, 8);
  }, [districts, q]);

  return (
    <Panel elevated className="w-64 p-2">
      <div className="flex items-center gap-2 rounded border border-line bg-void px-2 py-1.5">
        <Search size={14} className="text-ink-faint" aria-hidden />
        <input
          type="text"
          value={q}
          onFocus={() => setOpen(true)}
          onChange={(e) => {
            setQ(e.target.value);
            setOpen(true);
          }}
          placeholder="Jump to district…"
          aria-label="Search districts"
          className="flex-1 bg-transparent text-caption text-ink-primary outline-none placeholder:text-ink-faint"
        />
        {q ? (
          <button
            type="button"
            onClick={() => setQ("")}
            aria-label="Clear"
            className="text-ink-faint hover:text-ink-primary"
          >
            <X size={12} />
          </button>
        ) : null}
      </div>

      {open && matches.length ? (
        <ul className="mt-1 max-h-56 overflow-auto">
          {matches.map((f) => (
            <li key={f.properties.district_id}>
              <button
                type="button"
                onClick={() => {
                  onPick(f.properties.district_id, centroidOf(f));
                  setOpen(false);
                  setQ(f.properties.district_name);
                }}
                className={cn(
                  "w-full rounded px-2 py-1 text-left text-caption text-ink-muted",
                  "hover:bg-raised hover:text-ink-primary",
                )}
              >
                {f.properties.district_name}
              </button>
            </li>
          ))}
        </ul>
      ) : null}
    </Panel>
  );
}
