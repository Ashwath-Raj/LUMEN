/**
 * `FactorBars` (D2) — the §8 `Factor[]` that drive a score, as labelled weighted
 * bars. Each factor has a label, a signed weight (positive = pushes the score
 * up, negative = pulls it down), and optional detail. Bars are sorted by
 * magnitude so the dominant factors read first.
 *
 * Sign is shown by colour AND by an explicit +/− note (§F a11y — never colour
 * alone). Bar length is the |weight| normalised against the largest magnitude in
 * the set, so relative influence is legible without asserting an absolute scale
 * the spec does not define.
 */
import { Bar } from "./Bar";
import type { Factor } from "@/types/contracts";

interface FactorBarsProps {
  factors: Factor[];
}

export function FactorBars({ factors }: FactorBarsProps) {
  if (factors.length === 0) {
    return (
      <p className="text-caption text-ink-faint">No contributing factors listed.</p>
    );
  }

  const maxMagnitude = Math.max(...factors.map((f) => Math.abs(f.weight)), 1e-9);
  const sorted = [...factors].sort(
    (a, b) => Math.abs(b.weight) - Math.abs(a.weight),
  );

  return (
    <div className="flex flex-col gap-2" role="group" aria-label="Contributing factors">
      {sorted.map((factor, i) => {
        const positive = factor.weight >= 0;
        return (
          <div key={`${factor.label}-${i}`} className="flex flex-col gap-0.5">
            <Bar
              label={factor.label}
              value={Math.abs(factor.weight) / maxMagnitude}
              tone={positive ? "var(--confidence-high)" : "var(--risk-high)"}
              note={positive ? "increases" : "decreases"}
            />
            {factor.detail ? (
              <p className="pl-0.5 text-caption text-ink-faint">{factor.detail}</p>
            ) : null}
          </div>
        );
      })}
    </div>
  );
}
