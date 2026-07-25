/**
 * `MapCanvas` (D9, §30.3) — the Leaflet crime map. Owns react-leaflet + Leaflet
 * CSS + the geo theme, so it is code-split into the geo chunk (arch §G). The
 * GeoPage lazy-loads it.
 *
 * ── Disappearing-overlay fix  ─────────────────────────────────
 * Overlays are rendered with the DEFAULT SVG renderer (NOT `preferCanvas`): SVG
 * vector layers transform with the map via CSS at every zoom level and never
 * blank out, unlike the canvas renderer which cleared vectors during zoom. The
 * boundaries also live in a dedicated pane and are NOT re-keyed on zoom, so they
 * are created once and simply transform. Combined with authentic dense district
 * geometry (borders are always on-screen), overlays stay visible at every zoom.
 * ─────────────────────────────────────────────────────────────────────────
 *
 * Layers over three basemaps (dark default): Karnataka state + district
 * BOUNDARIES (always, from static authentic GeoJSON), risk CHOROPLETH (live join),
 * incident points (clustered), density heatmap-style, hotspot clusters, station
 * catchment, reporting delay. Interaction: pan/zoom (→URL), district hover
 * highlight + click-drill, selected-district cyan glow, marker click → Inspector,
 * incident click → workspace. maxBounds + zoom limits prevent world scrolling.
 */
import { useEffect, useMemo } from "react";
import {
  Circle,
  CircleMarker,
  GeoJSON,
  MapContainer,
  Pane,
  TileLayer,
  Tooltip,
  useMap,
  useMapEvents,
} from "react-leaflet";
import L, { type Layer, type PathOptions } from "leaflet";
import type { Feature, Geometry } from "geojson";

import type { EntityRef } from "@/components/entity";
import type {
  GeoDelayResult,
  GeoDistrict,
  GeoHotspotsResult,
  GeoLayer,
  GeoUnitsResult,
} from "@/types/geo";

import { BASEMAPS, type BasemapId } from "./basemaps";
import { clusterIncidents } from "./clustering";
import {
  GEO_MAX_ZOOM,
  GEO_MIN_ZOOM,
  KARNATAKA_BOUNDS,
  type DistrictFeatureProps,
} from "./data/karnataka";
import { lineColor, riskColor, signalColor } from "./geoStyle";
import type { GeoViewState } from "./geoUrlState";
import type { KarnatakaBoundaries } from "./useKarnatakaBoundaries";

import "leaflet/dist/leaflet.css";
import "./geo.css";

interface MapCanvasProps {
  view: GeoViewState;
  basemap: BasemapId;
  layers: GeoLayer[];
  /** Authentic reference boundaries (state + districts). */
  boundaries: KarnatakaBoundaries | undefined;
  /** Live choropleth data joined onto the district boundaries. */
  liveDistricts: GeoDistrict[] | undefined;
  hotspots: GeoHotspotsResult | undefined;
  units: GeoUnitsResult | undefined;
  delay: GeoDelayResult | undefined;
  /** The drilled/selected district id — rendered with a cyan glow. */
  selectedDistrict: string | null;
  onViewportChange: (center: [number, number], zoom: number) => void;
  onDistrictClick: (districtId: string) => void;
  onSelectEntity: (ref: EntityRef) => void;
  onOpenCase: (caseId: string) => void;
}

export function MapCanvas({
  view,
  basemap,
  layers,
  boundaries,
  liveDistricts,
  hotspots,
  units,
  delay,
  selectedDistrict,
  onViewportChange,
  onDistrictClick,
  onSelectEntity,
  onOpenCase,
}: MapCanvasProps) {
  const tile = BASEMAPS[basemap];
  const has = (layer: GeoLayer) => layers.includes(layer);

  // Join live choropleth data by any of the district's ids (census / LGD) or a
  // normalized name — robust to whichever key the backend emits.
  const liveByKey = useMemo(() => {
    const map = new Map<string, GeoDistrict>();
    for (const d of liveDistricts ?? []) {
      map.set(d.district_id, d);
      map.set(d.district_name.trim().toLowerCase(), d);
    }
    return map;
  }, [liveDistricts]);

  function liveFor(props: DistrictFeatureProps): GeoDistrict | undefined {
    return (
      liveByKey.get(props.district_id) ??
      liveByKey.get(String(props.lgd)) ??
      liveByKey.get(props.district_name.trim().toLowerCase())
    );
  }

  const choropleth = has("risk_choropleth");

  function districtStyle(
    feature?: Feature<Geometry, DistrictFeatureProps>,
  ): PathOptions {
    const props = feature?.properties;
    const selected = !!props && props.district_id === selectedDistrict;
    const live = props ? liveFor(props) : undefined;
    const filled = choropleth && !!live;
    return {
      color: selected ? signalColor() : lineColor(),
      weight: selected ? 2 : 1,
      // Thin cyan administrative borders (visual quality) — the signal accent at
      // low opacity for unselected districts, full for the selected one.
      opacity: selected ? 1 : 0.7,
      fillColor: filled ? riskColor(live!.risk_band) : signalColor(),
      fillOpacity: filled ? 0.5 : 0.04,
      className: selected ? "geo-district-selected" : "",
    };
  }

  function onEachDistrict(
    feature: Feature<Geometry, DistrictFeatureProps>,
    layer: Layer,
  ) {
    const props = feature.properties;
    const live = liveFor(props);
    const label = live
      ? `${props.district_name} · ${live.risk_band} · ${live.case_count} cases`
      : props.district_name;
    layer.bindTooltip(label, { sticky: true, className: "lumen-tip" });
    layer.on({
      click: () => onDistrictClick(props.district_id),
      mouseover: (e) => {
        const path = e.target as L.Path;
        path.setStyle({ weight: 2, color: signalColor(), fillOpacity: live ? 0.6 : 0.1 });
        path.bringToFront();
      },
      mouseout: (e) => {
        (e.target as L.Path).setStyle(districtStyle(feature));
      },
    });
  }

  return (
    <MapContainer
      center={view.center}
      zoom={view.zoom}
      minZoom={GEO_MIN_ZOOM}
      maxZoom={GEO_MAX_ZOOM}
      maxBounds={KARNATAKA_BOUNDS}
      maxBoundsViscosity={1.0}
      className="lumen-map h-full w-full"
      zoomControl
    >
      <TileLayer
        key={basemap}
        url={tile.url}
        attribution={tile.attribution}
        maxZoom={tile.maxZoom}
        noWrap
      />

      <ViewportSync onViewportChange={onViewportChange} />
      <ViewController center={view.center} zoom={view.zoom} />
      <FitOnMount hasExplicitView={view.hasExplicitViewport} />

      {/* Boundary pane (below data markers). Panes give deterministic z-order. */}
      <Pane name="boundaries" style={{ zIndex: 410 }}>
        {boundaries ? (
          <>
            {/* State administrative boundary — thicker cyan, non-interactive. */}
            <GeoJSON
              data={boundaries.state}
              interactive={false}
              style={{
                color: signalColor(),
                weight: 2,
                opacity: 0.9,
                fill: false,
              }}
            />
            {/* District boundaries + choropleth. Re-keyed only on selection /
                choropleth / live-data change (never on zoom), so it transforms
                smoothly and never disappears. */}
            <GeoJSON
              key={`districts-${choropleth}-${selectedDistrict ?? ""}-${liveDistricts?.length ?? 0}`}
              data={boundaries.districts}
              style={(f) =>
                districtStyle(f as Feature<Geometry, DistrictFeatureProps>)
              }
              onEachFeature={(f, l) =>
                onEachDistrict(f as Feature<Geometry, DistrictFeatureProps>, l)
              }
            />
          </>
        ) : null}
      </Pane>

      {/* Data pane (above boundaries). */}
      <Pane name="data" style={{ zIndex: 450 }}>
        {/* Incident points — client-clustered (§30.3). */}
        {has("incident_points") && hotspots
          ? clusterIncidents(hotspots.incidents, Math.round(view.zoom)).map((c) =>
              c.count === 1 ? (
                <CircleMarker
                  key={`inc-${c.id}`}
                  center={c.center}
                  radius={4}
                  pane="data"
                  pathOptions={{
                    color: c.members[0].risk_band
                      ? riskColor(c.members[0].risk_band)
                      : signalColor(),
                    fillOpacity: 0.85,
                    weight: 1,
                  }}
                  eventHandlers={{
                    click: () => onOpenCase(c.members[0].case_master_id),
                  }}
                >
                  <Tooltip className="lumen-tip">{c.members[0].crime_no}</Tooltip>
                </CircleMarker>
              ) : (
                <CircleMarker
                  key={`cl-${c.id}`}
                  center={c.center}
                  radius={Math.min(10 + Math.sqrt(c.count) * 3, 34)}
                  pane="data"
                  pathOptions={{
                    color: signalColor(),
                    fillColor: signalColor(),
                    fillOpacity: 0.25,
                    weight: 1,
                  }}
                >
                  <Tooltip className="lumen-tip" permanent direction="center">
                    {c.count}
                  </Tooltip>
                </CircleMarker>
              ),
            )
          : null}

        {/* Density (heatmap-style graduated bubbles) OR discrete hotspot
            clusters — mutually exclusive so the map doesn't double-render. */}
        {has("density")
          ? hotspots?.hotspots.map((h) => (
              <CircleMarker
                key={`density-${h.hotspot_id}`}
                center={h.center}
                radius={Math.min(6 + Math.sqrt(h.case_count) * 3, 40)}
                pane="data"
                pathOptions={{
                  color: riskColor(h.risk_band),
                  fillColor: riskColor(h.risk_band),
                  fillOpacity: 0.2,
                  weight: 0,
                }}
              />
            ))
          : hotspots?.hotspots.map((h) => (
              <Circle
                key={`cluster-${h.hotspot_id}`}
                center={h.center}
                radius={h.radius_m}
                pane="data"
                pathOptions={{
                  color: riskColor(h.risk_band),
                  fillColor: riskColor(h.risk_band),
                  fillOpacity: 0.15,
                  weight: 1,
                }}
                eventHandlers={{
                  click: () =>
                    onSelectEntity({
                      kind: "location",
                      id: h.hotspot_id,
                      label: `Hotspot · ${h.case_count} cases`,
                      sublabel: h.crime_head ?? undefined,
                      fields: [
                        { label: "cases", value: String(h.case_count) },
                        { label: "risk", value: h.risk_band },
                        { label: "radius", value: `${h.radius_m} m` },
                      ],
                    }),
                }}
              >
                <Tooltip className="lumen-tip">{`Hotspot · ${h.case_count} cases`}</Tooltip>
              </Circle>
            ))}

        {/* Station catchment (§30.3). */}
        {has("station_catchment") &&
          units?.units.map((u) => (
            <CircleMarker
              key={`unit-${u.unit_id}`}
              center={u.center}
              radius={7}
              pane="data"
              pathOptions={{
                color: signalColor(),
                fillColor: u.risk_band ? riskColor(u.risk_band) : signalColor(),
                fillOpacity: 0.5,
                weight: 1,
              }}
              eventHandlers={{
                click: () =>
                  onSelectEntity({
                    kind: "station",
                    id: u.unit_id,
                    label: u.unit_name,
                    sublabel: `${u.case_count} cases`,
                    href: `/cases?station=${u.unit_id}`,
                    fields: [
                      { label: "cases", value: String(u.case_count) },
                      { label: "unit id", value: u.unit_id, mono: true },
                    ],
                  }),
              }}
            >
              <Tooltip className="lumen-tip">{u.unit_name}</Tooltip>
            </CircleMarker>
          ))}

        {/* Reporting-delay layer (§3.2 fact 5) — the layer no other team has. */}
        {has("reporting_delay") &&
          delay?.units.map((u) => (
            <CircleMarker
              key={`delay-${u.unit_id}`}
              center={u.center}
              radius={8}
              pane="data"
              pathOptions={{
                color: u.anomalous ? riskColor("high") : lineColor(),
                fillColor: u.anomalous ? riskColor("high") : signalColor(),
                fillOpacity: 0.55,
                weight: u.anomalous ? 2 : 1,
              }}
              eventHandlers={{
                click: () =>
                  onSelectEntity({
                    kind: "station",
                    id: u.unit_id,
                    label: u.unit_name,
                    sublabel: `${u.median_delay_days}d median delay`,
                    fields: [
                      { label: "median delay", value: `${u.median_delay_days} days` },
                      { label: "anomalous", value: u.anomalous ? "yes" : "no" },
                    ],
                  }),
              }}
            >
              <Tooltip className="lumen-tip">{`${u.unit_name} · ${u.median_delay_days}d`}</Tooltip>
            </CircleMarker>
          ))}
      </Pane>
    </MapContainer>
  );
}

/** Publishes viewport changes (moveend) to the URL-state owner. */
function ViewportSync({
  onViewportChange,
}: {
  onViewportChange: (center: [number, number], zoom: number) => void;
}) {
  useMapEvents({
    moveend: (e) => {
      const c = e.target.getCenter();
      onViewportChange([c.lat, c.lng], e.target.getZoom());
    },
  });
  return null;
}

/** Drives the map imperatively on an external view change (drill/reset). */
function ViewController({
  center,
  zoom,
}: {
  center: [number, number];
  zoom: number;
}) {
  const map = useMap();
  useEffect(() => {
    const current = map.getCenter();
    if (
      Math.abs(current.lat - center[0]) > 0.05 ||
      Math.abs(current.lng - center[1]) > 0.05 ||
      map.getZoom() !== zoom
    ) {
      map.setView(center, zoom, { animate: true });
    }
  }, [map, center, zoom]);
  return null;
}

/** Fits Karnataka once on mount when the URL carries no explicit viewport. */
function FitOnMount({ hasExplicitView }: { hasExplicitView: boolean }) {
  const map = useMap();
  useEffect(() => {
    if (!hasExplicitView) {
      map.fitBounds(L.latLngBounds(KARNATAKA_BOUNDS), { animate: false });
    }
    // Fit only once, on mount.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);
  return null;
}
