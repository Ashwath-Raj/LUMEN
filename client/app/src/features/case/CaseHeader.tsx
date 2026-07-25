/**
 * Case Workspace header (E.4): CrimeNoDecoder · crime type · gravity · status ·
 * TrustBadge; registered date at station, district · IO; ClassificationBadge ·
 * QualityBadge. Feature assembly of Session-1/2 reusable components (§G).
 */
import { CrimeNoDecoder } from "@/components/case/CrimeNoDecoder";
import { ClassificationBadge, RiskBand } from "@/components/trust";
import type { CaseDetail } from "@/types/case";

function formatDate(iso: string | null): string {
  return iso ? iso.slice(0, 10) : "date unknown";
}

export function CaseHeader({ detail }: { detail: CaseDetail }) {
  const io = detail.officers.find((o) => o.role === "investigating");

  return (
    <header className="flex flex-col gap-2 border-b border-line px-6 py-4">
      <div className="flex flex-wrap items-center gap-3">
        <CrimeNoDecoder crimeNo={detail.crime_no} variant="full" />
        <span className="text-panel-title text-ink-primary">
          {detail.crime_type.head_name}
        </span>
        <span className="text-caption text-ink-muted">{detail.gravity.name}</span>
        <span className="text-caption text-ink-muted">·</span>
        <span className="text-caption text-ink-muted">{detail.status.name}</span>
        {detail.risk_band ? (
          <RiskBand band={detail.risk_band} />
        ) : null}
      </div>

      <div className="flex flex-wrap items-center gap-2 text-caption text-ink-muted">
        <span>
          Registered {formatDate(detail.crime_registered_date)} at{" "}
          {detail.station.unit_name}, {detail.station.district_name}
        </span>
        {io ? (
          <>
            <span aria-hidden>·</span>
            <span>IO {io.display_name}</span>
          </>
        ) : null}
      </div>

      <div className="flex flex-wrap items-center gap-2">
        <ClassificationBadge classification={detail.classification} />
      </div>
    </header>
  );
}
