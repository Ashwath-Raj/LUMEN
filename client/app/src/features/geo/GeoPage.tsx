/**
 * Geo Intelligence — `/geo` (E.2, §30.3). Full-bleed map with the four drill
 * levels (State → District → Station → Cluster), five toggleable layers, three
 * basemaps, a time scrubber, district search, and the persistent Inspector — the
 * map IS the navigation. Every view element serializes to the URL (§C): viewport,
 * layers, level, district, time range, basemap, and inspector selection.
 *
 * Boundaries come from AUTHENTIC static GeoJSON (always available); live
 * intelligence comes only from the canonical §29.1 `/geo/*` endpoints. While
 * those are unavailable (501), the map + Karnataka boundaries stay visible, a
 * non-blocking banner says so, and data layers are disabled — never a blank page
 * or table (the table fallback appears only if Leaflet itself fails to load).
 * The map bundle is lazy-loaded in its own chunk (arch §G).
 */
import { Suspense, lazy, useCallback, useMemo, useRef } from "react";
import { useNavigate, useSearchParams } from "react-router-dom";

import { useGeoDistricts, useGeoHotspots, useGeoUnits, useGeoDelay } from "@/api";
import { InspectorPanel } from "@/components/inspector";
import type { EntityRef } from "@/components/entity";
import { EmptyState } from "@/design/primitives";
import { useInspector } from "@/hooks/useInspector";
import type { GeoLayer } from "@/types/geo";

import { BasemapSwitcher } from "./controls/BasemapSwitcher";
import { DistrictSearch } from "./controls/DistrictSearch";
import { GeoDegradedBanner } from "./controls/GeoDegradedBanner";
import { LayerControl } from "./controls/LayerControl";
import { MapLegend } from "./controls/MapLegend";
import { TimeScrubber } from "./controls/TimeScrubber";
import { MapErrorBoundary } from "./MapErrorBoundary";
import { DEFAULT_BASEMAP, type BasemapId } from "./basemaps";
import { readGeoState, toggleLayer, writeGeoState } from "./geoUrlState";
import { useKarnatakaBoundaries } from "./useKarnatakaBoundaries";
import { readParam } from "@/utils/urlState";

// Lazy: Leaflet + react-leaflet land in the geo chunk only (arch §G budget).
const MapCanvas = lazy(() =>
  import("./MapCanvas").then((m) => ({ default: m.MapCanvas })),
);

export default function GeoPage() {
  const [params, setParams] = useSearchParams();
  const navigate = useNavigate();
  const view = useMemo(() => readGeoState(params), [params]);
  const basemap = (readParam(params, "base") as BasemapId) || DEFAULT_BASEMAP;

  const { selection, select, clear } = useInspector();
  const refCache = useRef<Map<string, EntityRef>>(new Map());

  // Authentic boundaries (static assets) — always available, independent of API.
  const boundariesQuery = useKarnatakaBoundaries();

  // ── Live geo queries (each drill level is a fresh query, §30.3) ──────────
  const districtsQuery = useGeoDistricts();
  const geoParams = {
    district: view.district ?? undefined,
    date_from: view.date_from ?? undefined,
    date_to: view.date_to ?? undefined,
  };
  const hotspotsQuery = useGeoHotspots(
    geoParams,
    view.layers.includes("incident_points") || view.layers.includes("density"),
  );
  const unitsQuery = useGeoUnits(
    view.layers.includes("station_catchment") ? view.district : null,
  );
  const delayQuery = useGeoDelay(
    geoParams,
    view.layers.includes("reporting_delay"),
  );

  // Which layers cannot be drawn (no data / errored) → disabled in the control.
  const unavailable = useMemo(() => {
    const set = new Set<GeoLayer>();
    if (districtsQuery.isError || !districtsQuery.data?.length)
      set.add("risk_choropleth");
    if (hotspotsQuery.isError || !hotspotsQuery.data?.incidents.length)
      set.add("incident_points");
    if (hotspotsQuery.isError || !hotspotsQuery.data?.hotspots.length)
      set.add("density");
    if (unitsQuery.isError || !unitsQuery.data?.units.length)
      set.add("station_catchment");
    if (delayQuery.isError || !delayQuery.data?.units.length)
      set.add("reporting_delay");
    return set;
  }, [
    districtsQuery.isError,
    districtsQuery.data,
    hotspotsQuery.isError,
    hotspotsQuery.data,
    unitsQuery.isError,
    unitsQuery.data,
    delayQuery.isError,
    delayQuery.data,
  ]);

  // Degraded when no live geo intelligence is available and nothing is loading.
  // Self-heals: once any live geo endpoint returns data, the banner hides.
  const liveGeoLoading = districtsQuery.isLoading || hotspotsQuery.isLoading;
  const anyLiveGeo =
    (districtsQuery.data?.length ?? 0) > 0 ||
    (hotspotsQuery.data?.hotspots.length ?? 0) > 0 ||
    (hotspotsQuery.data?.incidents.length ?? 0) > 0;
  const degraded = !liveGeoLoading && !anyLiveGeo;

  // ── View + selection actions (all through the URL) ───────────────────────
  const onViewportChange = useCallback(
    (center: [number, number], zoom: number) => {
      setParams((prev) => writeGeoState(prev, { center, zoom }), {
        replace: true,
      });
    },
    [setParams],
  );

  const onDistrictClick = useCallback(
    (districtId: string) => {
      setParams((prev) =>
        writeGeoState(prev, { district: districtId, level: "district" }),
      );
    },
    [setParams],
  );

  const onSelectEntity = useCallback(
    (ref: EntityRef) => {
      refCache.current.set(`${ref.kind}:${ref.id}`, ref);
      select(ref);
    },
    [select],
  );

  function setBasemap(id: BasemapId) {
    setParams((prev) => {
      const next = new URLSearchParams(prev);
      if (id === DEFAULT_BASEMAP) next.delete("base");
      else next.set("base", id);
      return next;
    });
  }

  function onToggleLayer(layer: GeoLayer) {
    setParams((prev) =>
      writeGeoState(prev, { layers: toggleLayer(view.layers, layer) }),
    );
  }

  // Resolve the URL inspector selection to a rich ref from the session cache.
  const selectedRef: EntityRef | null = useMemo(() => {
    if (!selection) return null;
    const token = `${selection.kind}:${selection.id}`;
    return (
      refCache.current.get(token) ?? {
        kind: selection.kind,
        id: selection.id,
        label: selection.id,
      }
    );
  }, [selection]);

  const liveDistricts = districtsQuery.data ?? [];

  return (
    // `isolate` scopes the geo overlay's z-index to this subtree; combined with
    // the isolated map container, the controls overlay reliably sits above the
    // map at every zoom level (see geo.css for the full root-cause note).
    <div className="relative isolate min-h-0 w-full flex-1 overflow-hidden">
      {/* The map (lazy Leaflet chunk); table fallback only if Leaflet fails. */}
      <MapErrorBoundary districts={liveDistricts}>
        <Suspense
          fallback={
            <div className="flex h-full items-center justify-center">
              <EmptyState message="Loading map…" />
            </div>
          }
        >
          <MapCanvas
            view={view}
            basemap={basemap}
            layers={view.layers}
            boundaries={boundariesQuery.data}
            liveDistricts={districtsQuery.data}
            hotspots={hotspotsQuery.data}
            units={unitsQuery.data}
            delay={delayQuery.data}
            selectedDistrict={view.district}
            onViewportChange={onViewportChange}
            onDistrictClick={onDistrictClick}
            onSelectEntity={onSelectEntity}
            onOpenCase={(caseId) => navigate(`/case/${caseId}`)}
          />
        </Suspense>
      </MapErrorBoundary>

      {/* ── Overlaid controls (responsive: wrap/stack on narrow widths) ────── */}
      <div className="pointer-events-none absolute inset-0 z-inspector">
        {/* Top-left: layers + district search */}
        <div className="pointer-events-auto absolute left-4 top-4 flex max-w-[calc(100%-2rem)] flex-col gap-2">
          <LayerControl
            active={view.layers}
            unavailable={unavailable}
            onToggle={onToggleLayer}
          />
          <DistrictSearch
            districts={boundariesQuery.data?.districts}
            onPick={(districtId, center) =>
              setParams((prev) =>
                writeGeoState(prev, {
                  district: districtId,
                  level: "district",
                  center,
                  zoom: 9,
                }),
              )
            }
          />
        </div>

        {/* Top-right: basemap + degraded banner */}
        <div className="pointer-events-auto absolute right-4 top-4 flex max-w-[calc(100%-2rem)] flex-col items-end gap-2">
          <BasemapSwitcher active={basemap} onChange={setBasemap} />
          {degraded ? (
            <GeoDegradedBanner
              detail={
                view.district ? "Showing district boundaries only." : undefined
              }
            />
          ) : null}
        </div>

        {/* Bottom-centre: legend + time scrubber */}
        <div className="pointer-events-auto absolute inset-x-4 bottom-4 flex flex-col items-center gap-2">
          <MapLegend />
          <div className="w-full max-w-2xl">
            <TimeScrubber
              from={view.date_from}
              onCommit={(from) =>
                setParams((prev) => writeGeoState(prev, { date_from: from }))
              }
            />
          </div>
        </div>

        {/* Right: persistent Inspector (overlay mode) — shown on selection. */}
        {selectedRef ? (
          <div className="pointer-events-auto absolute inset-y-0 right-0 max-w-full">
            <InspectorPanel entity={selectedRef} onClose={clear} />
          </div>
        ) : null}
      </div>
    </div>
  );
}
