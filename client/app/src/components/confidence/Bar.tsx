/**
 * `Bar` — a single labelled 0–1 horizontal bar, the shared building block of the
 * confidence meter, the confidence breakdown, and the factor bars. Bar markup
 * (track, fill, value readout, 0–1 clamp) lives here once (no duplicated UI).
 *
 * The fill colour is a token var supplied by the caller; the numeric value is
 * always shown as text next to the bar (§F a11y — never colour/length alone).
 * `emphasis` marks the limiting/weakest bar without relying on colour.
 */
import { cn } from "@/utils/cn";

interface BarProps {
  label: string;
  /** 0–1. Values outside the range are clamped for the fill only. */
  value: number;
  /** Token colour var for the fill, e.g. `var(--confidence-high)`. */
  tone: string;
  /** Optional trailing note, e.g. "limiting" or a Factor weight sign. */
  note?: string;
  /** Visually mark this as the notable bar (e.g. the limiting component). */
  emphasis?: boolean;
}

export function Bar({ label, value, tone, note, emphasis = false }: BarProps) {
  const pct = Math.max(0, Math.min(1, value)) * 100;
  return (
    <div className="flex flex-col gap-1">
      <div className="flex items-baseline justify-between text-caption">
        <span
          className={cn(
            emphasis ? "text-ink-primary" : "text-ink-muted",
            emphasis && "font-medium",
          )}
        >
          {label}
          {note ? <span className="text-ink-faint"> · {note}</span> : null}
        </span>
        <span className="font-mono text-ink-muted">{value.toFixed(2)}</span>
      </div>
      <div
        className="h-1.5 w-full overflow-hidden rounded bg-raised"
        role="meter"
        aria-label={label}
        aria-valuenow={Number(value.toFixed(2))}
        aria-valuemin={0}
        aria-valuemax={1}
      >
        <div
          className="h-full rounded"
          style={{ width: `${pct}%`, background: tone }}
        />
      </div>
    </div>
  );
}
