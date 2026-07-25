/**
 * Case Workspace summary strip (E.4) — the at-a-glance risk/confidence/quality
 * summary plus entity counts, each a clickable `Stat` (§F "always clickable",
 * §30.2 "every element is an entry point"). Risk/confidence/quality jump to the
 * Insights tab (where the decomposition lives); counts jump to Overview.
 *
 * Derived values render "—" when the case has no insight yet — never fabricated.
 */
import { Stat } from "@/design/primitives";
import { RISK_LABEL } from "@/design/tokens";
import type { CaseDetail } from "@/types/case";

interface CaseSummaryStripProps {
  detail: CaseDetail;
  onGoToTab: (tab: string) => void;
}

export function CaseSummaryStrip({ detail, onGoToTab }: CaseSummaryStripProps) {
  return (
    <div className="grid grid-cols-2 gap-2 px-6 py-3 md:grid-cols-3 xl:grid-cols-5">
      <Stat
        label="Risk"
        value={detail.risk_band ? RISK_LABEL[detail.risk_band] : "—"}
        hint="decomposed on Insights"
        onClick={() => onGoToTab("insights")}
      />
      <Stat
        label="Officers"
        value={detail.officers.length}
        hint="assigned"
        onClick={() => onGoToTab("overview")}
      />
      <Stat
        label="Charges"
        value={detail.charges.length}
        hint="acts & sections"
        onClick={() => onGoToTab("overview")}
      />
      <Stat
        label="People"
        value={detail.participants.length}
        hint="victims · accused · complainants"
        onClick={() => onGoToTab("overview")}
      />
    </div>
  );
}
