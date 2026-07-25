/**
 * `IdentityBanner` (D6, §6.4) — always shown first on a Person Dossier: an
 * inferred, uncertain identity rendered WITH its confidence (P10), the count of
 * linked records, a "see why" affordance (match features), and a "report
 * incorrect match" control (→ `POST /persons/{id}/dispute`). Language follows
 * §6.4 — "associated with N case records", never "criminal".
 *
 * Trust is rendered, not claimed (§11): the identity caveat is a component
 * default. Confidence uses the shared §9 band vocabulary.
 */
import { ShieldQuestion } from "lucide-react";

import { ConfidenceMeter } from "@/components/confidence";
import { TrustBadge } from "@/components/trust";
import { Button, Panel } from "@/design/primitives";
import { CONFIDENCE_TOKEN, confidenceBand } from "@/design/tokens";
import type { PersonDetail } from "@/types/person";

interface IdentityBannerProps {
  person: PersonDetail;
  onDispute?: () => void;
  onSeeWhy?: () => void;
}

export function IdentityBanner({ person, onDispute, onSeeWhy }: IdentityBannerProps) {
  const conf = person.resolution_confidence;
  const band = confidenceBand(conf);

  return (
    <Panel elevated className="flex flex-col gap-3 p-4">
      <div className="flex items-start gap-3">
        <ShieldQuestion size={22} strokeWidth={1.5} className="mt-0.5 text-signal" aria-hidden />
        <div className="flex min-w-0 flex-1 flex-col gap-0.5">
          <div className="flex items-center gap-2">
            <span className="text-panel-title text-ink-primary">
              {person.canonical_name}
            </span>
            <span className="font-mono text-caption text-ink-faint">
              {person.person_id}
            </span>
          </div>
          <p className="text-caption text-ink-muted">
            Inferred identity · {person.description} · across{" "}
            {person.district_count} district{person.district_count === 1 ? "" : "s"}
          </p>
        </div>
        <span
          className="font-mono text-body"
          style={{ color: CONFIDENCE_TOKEN[band] }}
          title="Resolution confidence (P10)"
        >
          {conf.toFixed(2)}
        </span>
      </div>

      {/* Confidence is never a bare number (§9) — show the meter. The breakdown
          isn't part of the person contract, so the meter stays compact here. */}
      <div className="max-w-md">
        <ConfidenceMeter
          breakdown={{
            evidence_quality: conf,
            model_confidence: conf,
            data_completeness: conf,
            identity_confidence: conf,
            graph_confidence: conf,
            composite: conf,
          }}
        />
      </div>

      <TrustBadge context="identity" suffix={`Confidence ${conf.toFixed(2)}.`} />

      <div className="flex flex-wrap gap-2">
        {onSeeWhy ? (
          <Button variant="secondary" onClick={onSeeWhy}>
            See matching evidence
          </Button>
        ) : null}
        {onDispute ? (
          <Button variant="ghost" onClick={onDispute}>
            Report incorrect match
          </Button>
        ) : null}
      </div>
    </Panel>
  );
}
