/**
 * Admin — `/admin` (E.10, §20/§21). The audit read surface. `GET /audit` is
 * REAL and gated by the policy engine: only a caller whose `lumen_user_role`
 * grants `read_audit` (the Auditor role) is served; every other identity is
 * denied AND the denial itself is audited (§20.2) — governance made visible.
 *
 * The deployed identity binding is Catalyst Authentication → user_id; in this
 * environment no operator↔role binding exists yet, so the surface states that
 * as a governance condition (calm, §B "scope denial is a feature"), not an
 * error. No audit rows are fabricated.
 */
import { Lock, ShieldCheck } from "lucide-react";

import { Panel } from "@/design/primitives";

export default function AdminPage() {
  return (
    <div className="min-h-0 flex-1 overflow-auto">
      <div className="mx-auto flex max-w-3xl flex-col gap-4 p-6">
        <h1 className="font-display text-page-title text-ink-primary">Admin</h1>

        <Panel className="flex flex-col gap-3 p-4">
          <h2 className="flex items-center gap-2 text-body text-ink-primary">
            <Lock size={16} className="text-signal" aria-hidden />
            Audit log · Auditor role only
          </h2>
          <p className="text-caption text-ink-muted">
            The audit surface (<span className="font-mono">GET /audit</span>) is
            live and policy-gated (§20.2): it serves only an identity holding the
            Auditor role in <span className="font-mono">lumen_user_role</span>,
            and records every denial in the audit log itself. Access is logged.
          </p>
          <p className="text-caption text-ink-muted">
            This session has no operator-to-role binding yet — the deployed
            binding comes from Catalyst Authentication. Once an Auditor identity
            is bound, the access log (who read which case, who ran which AI
            query, who was denied) renders here.
          </p>
        </Panel>

        <Panel className="flex flex-col gap-2 p-4">
          <h2 className="flex items-center gap-2 text-body text-ink-primary">
            <ShieldCheck size={16} className="text-signal" aria-hidden />
            Role administration
          </h2>
          <p className="text-caption text-ink-muted">
            Roles are the §20.1 set (State Analyst · District SP · Investigating
            Officer · Station Officer · Auditor), held in{" "}
            <span className="font-mono">lumen_user_role</span> and enforced
            server-side by the single policy authoriser. No role-management
            endpoint is exposed; assignments are a deployment operation.
          </p>
        </Panel>
      </div>
    </div>
  );
}
