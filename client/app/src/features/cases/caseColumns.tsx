/**
 * Case Registry grid columns (E.3): CrimeNo · title · district · station ·
 * status · priority · officer · created · updated · risk · confidence · quality.
 * Kept beside the page as feature assembly (arch §G: feature folders own page
 * assembly; the reusable renderers — CrimeNoDecoder, RiskBand, QualityBadge —
 * come from `components/`).
 *
 * Derived columns (risk/confidence/quality) render "—" when the case has no
 * insight yet — never a fabricated value (a case genuinely may have none).
 */
import type { Column } from "@/design/primitives";
import { CrimeNoDecoder } from "@/components/case/CrimeNoDecoder";
import { RiskBand } from "@/components/trust";
import type { CaseListItem } from "@/types/case";

function shortDate(iso: string | null): string {
  if (!iso) return "—";
  // Display-only; the value is already an ISO string from the envelope.
  return iso.slice(0, 10);
}

export const CASE_COLUMNS: Column<CaseListItem>[] = [
  {
    key: "crime_no",
    header: "Crime No",
    sortable: true,
    render: (c) => <CrimeNoDecoder crimeNo={c.crime_no} variant="compact" />,
  },
  {
    key: "title",
    header: "Title",
    sortable: true,
    render: (c) => <span className="text-ink-primary">{c.title}</span>,
  },
  {
    key: "district",
    header: "District",
    render: (c) => <span className="text-ink-muted">{c.district_name}</span>,
  },
  {
    key: "station",
    header: "Station",
    render: (c) => <span className="text-ink-muted">{c.station_name}</span>,
  },
  {
    key: "status",
    header: "Status",
    sortable: true,
    render: (c) => <span className="text-ink-muted">{c.status.name}</span>,
  },
  {
    key: "gravity",
    header: "Priority",
    sortable: true,
    render: (c) => <span className="text-ink-muted">{c.gravity.name}</span>,
  },
  {
    key: "officer",
    header: "Officer",
    render: (c) => (
      <span className="text-ink-muted">{c.officer_name ?? "Unassigned"}</span>
    ),
  },
  {
    key: "crime_registered_date",
    header: "Created",
    sortable: true,
    render: (c) => (
      <span className="font-mono text-ink-muted">
        {shortDate(c.crime_registered_date)}
      </span>
    ),
  },
  {
    key: "updated_at",
    header: "Updated",
    sortable: true,
    render: (c) => (
      <span className="font-mono text-ink-muted">{shortDate(c.updated_at)}</span>
    ),
  },
  {
    key: "risk",
    header: "Risk",
    sortable: true,
    render: (c) =>
      c.risk_band ? (
        <RiskBand band={c.risk_band} />
      ) : (
        <span className="text-ink-faint">—</span>
      ),
  },
  {
    key: "insights",
    header: "Insights",
    render: (c) => (
      <span className="font-mono text-ink-muted">{c.insight_count}</span>
    ),
  },
];
