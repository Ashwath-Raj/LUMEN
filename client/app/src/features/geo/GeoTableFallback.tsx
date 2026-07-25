/**
 * Geo table fallback (arch D9 "Table fallback (DataGrid of nodes/edges) … the
 * accessible alternative"). Per the Session-3 brief this renders ONLY when
 * Leaflet itself cannot load — not on a data 501 (that keeps the map visible).
 * It presents the same district data as a keyboard-navigable grid, so the geo
 * intelligence stays reachable without a canvas.
 */
import { useNavigate } from "react-router-dom";

import { RiskBand } from "@/components/trust";
import { DataGrid, type Column } from "@/design/primitives";
import type { GeoDistrict } from "@/types/geo";

const COLUMNS: Column<GeoDistrict>[] = [
  {
    key: "district_name",
    header: "District",
    render: (d) => <span className="text-ink-primary">{d.district_name}</span>,
  },
  {
    key: "risk",
    header: "Risk",
    render: (d) => <RiskBand band={d.risk_band} />,
  },
  {
    key: "case_count",
    header: "Cases",
    render: (d) => <span className="font-mono text-ink-muted">{d.case_count}</span>,
  },
];

export function GeoTableFallback({ districts }: { districts: GeoDistrict[] }) {
  const navigate = useNavigate();
  return (
    <div className="h-full overflow-auto p-6">
      <p className="mb-3 text-caption text-ink-muted">
        Map view unavailable — showing the district risk table (same data,
        keyboard-navigable).
      </p>
      {districts.length === 0 ? (
        <div className="rounded border border-line bg-panel px-4 py-8 text-center text-caption text-ink-muted">
          District intelligence isn’t available yet. It will populate here once
          the geo endpoints are live.
        </div>
      ) : (
      <div className="rounded border border-line bg-panel">
        <DataGrid<GeoDistrict>
          columns={COLUMNS}
          rows={districts}
          rowKey={(d) => d.district_id}
          caption="District risk (map fallback)"
          onOpen={(d) => navigate(`/cases?district=${d.district_id}`)}
        />
      </div>
      )}
    </div>
  );
}
