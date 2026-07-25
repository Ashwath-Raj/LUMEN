/**
 * `RequireRole` — permission wrapper (arch shared infra; spec §20 RBAC).
 * Restricts a surface to specific roles (e.g. `/admin` audit → Auditor). When
 * the role is out of scope it renders the calm governance notice, NOT a failure
 * (arch §B: "scope denial is a feature, not an error") — mirroring the
 * SCOPE_DENIED ErrorState so client-side and server-side denials look identical.
 *
 * Authoritative enforcement is server-side (spec §20); this wrapper is a UX
 * guard that keeps out-of-scope surfaces from rendering, not the security
 * boundary.
 */
import type { ReactNode } from "react";
import { Lock } from "lucide-react";

import { useSession } from "@/providers/sessionContext";
import type { Role } from "@/types/session";

export function RequireRole({
  allow,
  children,
}: {
  allow: Role[];
  children: ReactNode;
}) {
  const { role } = useSession();

  // Role is populated by the session/login sessions; until then, defer to the
  // server (render children — the endpoints themselves return SCOPE_DENIED,
  // which the ErrorState renders as the same governance notice).
  if (role !== null && !allow.includes(role)) {
    return (
      <div className="flex flex-col items-start gap-2 rounded border border-signal/40 bg-panel px-4 py-3">
        <div className="flex items-center gap-2 text-body text-ink-primary">
          <Lock size={16} />
          <span>Outside your role scope</span>
        </div>
        <p className="text-caption text-ink-muted">Access is logged.</p>
      </div>
    );
  }
  return <>{children}</>;
}
