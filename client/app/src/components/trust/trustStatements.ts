/**
 * §11 trust statements + the kind→context mapping, kept separate from the
 * `TrustBadge` component so that file stays component-only (React Fast Refresh).
 * These are literal component-DEFAULT strings so a caveat can never be forgotten
 * (§B "Trust is rendered, not claimed").
 */
import type { InsightKind } from "@/types/contracts";

export type TrustContext =
  | "network"
  | "identity"
  | "forecast"
  | "recommendation"
  | "act_section";

/** §11 literal statements. */
export const TRUST_STATEMENT: Record<TrustContext, string> = {
  network: "Co-accusal reflects charging decisions, not adjudicated guilt.",
  identity: "Inferred match. Report if incorrect.",
  forecast:
    "Trained on 14 months. Not valid for districts with fewer than 50 records.",
  recommendation: "Suggestion for officer review. Not an instruction.",
  act_section:
    "Reflects statistical co-occurrence in past filings. Not legal advice.",
};

/** The default trust context for an insight kind, or null if none applies. */
export function trustContextFor(kind: InsightKind): TrustContext | null {
  switch (kind) {
    case "network":
    case "linkage":
      return "network";
    case "forecast":
      return "forecast";
    case "recommendation":
      return "recommendation";
    default:
      return null;
  }
}
