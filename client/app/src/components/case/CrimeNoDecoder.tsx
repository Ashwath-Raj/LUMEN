/**
 * `CrimeNoDecoder` (D5) — the signature device (§31.3). Renders an 18-digit
 * CrimeNo as segmented mono — FIR · District · Unit · Year · Serial — each
 * segment labelled on hover and clickable as a filter into `/cases?…`. Proves
 * within five seconds that the real schema was read; doubles as navigation.
 *
 *   1 · 0443 · 0006 · 2026 · 00001
 *   FIR  Distr  Unit   Year   Serial   (§31.3)
 *
 * A `mismatch` flag (the backend's Q04 result: embedded district/unit ≠
 * `Unit.DistrictID`) renders an inline warning glyph — the decoder never
 * re-derives Q04 itself (that is a §5.1 backend rule), it only surfaces it.
 *
 * Used in the case header and case rows ONLY (§31.3, arch D5). Segments link via
 * react-router so navigation stays client-side; a malformed number (not 18
 * digits — Q03) renders as plain mono without segmentation rather than crashing.
 */
import { Link } from "react-router-dom";
import { TriangleAlert } from "lucide-react";

import { cn } from "@/utils/cn";

interface CrimeNoDecoderProps {
  crimeNo: string;
  /** Backend Q04 result — embedded district/unit disagrees with the record. */
  mismatch?: boolean;
  /** Compact (rows) hides the segment labels; full (header) shows them. */
  variant?: "compact" | "full";
  className?: string;
}

interface Segment {
  key: string;
  label: string;
  value: string;
  /** Query param this segment filters on, or null if not a filter. */
  filterKey: "district" | "station" | null;
}

/** §31.3 layout: FIR(1) · District(4) · Unit(4) · Year(4) · Serial(5) = 18. */
function decode(crimeNo: string): Segment[] | null {
  const digits = crimeNo.trim();
  if (!/^\d{18}$/.test(digits)) return null;
  return [
    { key: "fir", label: "FIR", value: digits.slice(0, 1), filterKey: null },
    { key: "district", label: "District", value: digits.slice(1, 5), filterKey: "district" },
    { key: "unit", label: "Unit", value: digits.slice(5, 9), filterKey: "station" },
    { key: "year", label: "Year", value: digits.slice(9, 13), filterKey: null },
    { key: "serial", label: "Serial", value: digits.slice(13, 18), filterKey: null },
  ];
}

export function CrimeNoDecoder({
  crimeNo,
  mismatch = false,
  variant = "full",
  className,
}: CrimeNoDecoderProps) {
  const segments = decode(crimeNo);

  // Q03 malformed: render plain, do not crash or fake segmentation.
  if (!segments) {
    return (
      <span className={cn("font-mono text-ink-primary", className)}>
        {crimeNo}
      </span>
    );
  }

  const full = variant === "full";

  return (
    <span
      className={cn("inline-flex items-center gap-1 font-mono", className)}
      aria-label={`Crime number ${crimeNo}`}
    >
      {segments.map((seg, i) => {
        const inner = (
          <span className="flex flex-col items-center leading-none">
            <span className="text-ink-primary">{seg.value}</span>
            {full ? (
              <span className="mt-0.5 text-[10px] uppercase tracking-wide text-ink-faint">
                {seg.label}
              </span>
            ) : null}
          </span>
        );

        return (
          <span key={seg.key} className="flex items-center gap-1">
            {seg.filterKey ? (
              <Link
                to={`/cases?${seg.filterKey}=${seg.value}`}
                title={`Filter by ${seg.label} ${seg.value}`}
                className="rounded px-0.5 hover:bg-raised hover:text-signal"
              >
                {inner}
              </Link>
            ) : (
              <span title={seg.label} className="px-0.5">
                {inner}
              </span>
            )}
            {i < segments.length - 1 ? (
              <span aria-hidden className="text-ink-faint">
                ·
              </span>
            ) : null}
          </span>
        );
      })}

      {mismatch ? (
        <TriangleAlert
          size={14}
          strokeWidth={1.5}
          className="ml-1 text-risk-high"
          aria-label="CrimeNo unit/district mismatch (quality rule Q04)"
        />
      ) : null}
    </span>
  );
}
