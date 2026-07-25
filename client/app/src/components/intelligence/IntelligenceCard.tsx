/**
 * `IntelligenceCard` — one workbench exchange rendered as an intelligence
 * REPORT, not a chat bubble (§30.7 "report card"; the brief's "no consumer chat
 * UI"). Query echo header → answer prose → confidence + source attribution →
 * collapsible `ReasoningPanel` → `EvidencePanel` → limitations → the standing
 * uncertainty disclaimer. Analyst actions: copy · retry · pin · export.
 *
 * The answer is the frozen §8 `Insight` from the REAL `/ai/ask`; every §A
 * question is answered structurally (evidence, decomposed confidence,
 * limitations, lineage), and an AI conclusion is NEVER presented as fact — the
 * disclaimer and the §16.4 fallback method are component defaults that cannot
 * be forgotten (§B "trust is rendered, not claimed").
 */
import { Copy, Pin, PinOff, RotateCcw, Download, Check } from "lucide-react";
import { useState, type ReactNode } from "react";

import { LimitationsNote } from "@/components/insight";
import { LifecycleBadge } from "@/components/trust";
import { Panel } from "@/design/primitives";
import type { Evidence } from "@/types/contracts";
import type { Exchange } from "@/types/intelligence";
import { cn } from "@/utils/cn";

import { ConfidenceBadge } from "./ConfidenceBadge";
import { EvidencePanel } from "./EvidencePanel";
import { ReasoningPanel } from "./ReasoningPanel";
import { SourceBadge } from "./SourceBadge";

interface IntelligenceCardProps {
  exchange: Exchange;
  pinned: boolean;
  onPin: (id: string) => void;
  onRetry: (exchange: Exchange) => void;
  onEvidenceActivate?: (evidence: Evidence) => void;
}

function exportExchange(exchange: Exchange) {
  const blob = new Blob([JSON.stringify(exchange, null, 2)], {
    type: "application/json",
  });
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = `lumen-intelligence-${exchange.id}.json`;
  a.click();
  URL.revokeObjectURL(url);
}

export function IntelligenceCard({
  exchange,
  pinned,
  onPin,
  onRetry,
  onEvidenceActivate,
}: IntelligenceCardProps) {
  const [copied, setCopied] = useState(false);
  const insight = exchange.insight;

  async function copyAnswer() {
    if (!insight) return;
    const text = [
      `Q: ${exchange.question}`,
      `A: ${insight.headline}`,
      `Confidence: ${insight.confidence.toFixed(2)} (composite, §9)`,
      `Method: ${insight.lineage.method} · ${insight.lineage.model_version}`,
      `Limitations: ${insight.limitations.join("; ")}`,
      `AI-assisted analysis for officer review — not a factual finding.`,
    ].join("\n");
    try {
      await navigator.clipboard.writeText(text);
      setCopied(true);
      window.setTimeout(() => setCopied(false), 1500);
    } catch {
      /* clipboard unavailable — non-fatal */
    }
  }

  return (
    <Panel className={cn("flex flex-col gap-3 p-4", pinned && "border-signal/50")}>
      {/* Query echo — mono, terminal register, not a chat bubble. */}
      <div className="flex items-baseline gap-2 border-b border-line pb-2">
        <span className="font-mono text-caption text-ink-faint">
          {exchange.asked_at.slice(11, 19)}
        </span>
        <span className="font-mono text-caption text-signal">query</span>
        <span className="min-w-0 flex-1 truncate text-caption text-ink-muted">
          {exchange.question}
        </span>
        {exchange.scope_districts.length ? (
          <span className="shrink-0 text-caption text-ink-faint">
            scope: {exchange.scope_districts.join(", ")}
          </span>
        ) : null}
      </div>

      {exchange.status === "pending" ? (
        <p className="text-caption text-ink-muted">Analysing…</p>
      ) : exchange.status === "failed" || !insight ? (
        <div className="flex items-center gap-3">
          <p className="text-caption text-risk-high">
            {exchange.error ?? "The analysis could not be completed."}
          </p>
          <button
            type="button"
            onClick={() => onRetry(exchange)}
            className="inline-flex items-center gap-1 text-caption text-signal hover:underline"
          >
            <RotateCcw size={12} aria-hidden /> Retry
          </button>
        </div>
      ) : (
        <>
          {/* Answer */}
          <p className="text-body text-ink-primary">{insight.headline}</p>

          <div className="flex flex-wrap items-center gap-2">
            <ConfidenceBadge value={insight.confidence} />
            <SourceBadge insight={insight} />
            <LifecycleBadge state={insight.lifecycle_state} />
          </div>

          <ReasoningPanel insight={insight} />
          <EvidencePanel
            evidence={insight.evidence}
            onActivate={onEvidenceActivate}
          />
          <LimitationsNote limitations={insight.limitations} />

          {/* Standing uncertainty disclaimer — a component default (§11). */}
          <p className="border-t border-line pt-2 text-caption text-ink-faint">
            AI-assisted analysis for officer review — an inference, not a
            factual finding. Verify against the cited records before acting.
          </p>

          {/* Analyst actions */}
          <div className="flex items-center gap-2">
            <ActionButton onClick={copyAnswer} label={copied ? "Copied" : "Copy"}>
              {copied ? <Check size={13} aria-hidden /> : <Copy size={13} aria-hidden />}
            </ActionButton>
            <ActionButton onClick={() => onRetry(exchange)} label="Retry">
              <RotateCcw size={13} aria-hidden />
            </ActionButton>
            <ActionButton onClick={() => onPin(exchange.id)} label={pinned ? "Unpin" : "Pin"}>
              {pinned ? <PinOff size={13} aria-hidden /> : <Pin size={13} aria-hidden />}
            </ActionButton>
            <ActionButton onClick={() => exportExchange(exchange)} label="Export">
              <Download size={13} aria-hidden />
            </ActionButton>
          </div>
        </>
      )}
    </Panel>
  );
}

function ActionButton({
  onClick,
  label,
  children,
}: {
  onClick: () => void;
  label: string;
  children: ReactNode;
}) {
  return (
    <button
      type="button"
      onClick={onClick}
      className="inline-flex items-center gap-1 rounded border border-line px-2 py-1 text-caption text-ink-muted transition-colors duration-DEFAULT ease-ease hover:border-signal/40 hover:text-ink-primary"
    >
      {children}
      {label}
    </button>
  );
}
