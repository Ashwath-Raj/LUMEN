/**
 * `RequireAuth` — authentication wrapper (arch shared infra). Gates the
 * authenticated shell: an unauthenticated visitor is sent to `/login`; while the
 * session is resolving, a neutral loading state shows (never a bare spinner).
 * Auth itself is Catalyst Authentication (spec §26.1 row 17) via the session
 * provider — this wrapper only enforces presence, never re-implements auth.
 */
import type { ReactNode } from "react";
import { Navigate, useLocation } from "react-router-dom";

import { useSession } from "@/providers/sessionContext";
import { EmptyState } from "@/design/primitives";

export function RequireAuth({ children }: { children: ReactNode }) {
  const { operator, loading } = useSession();
  const location = useLocation();

  if (loading) {
    return <EmptyState message="Checking your session…" />;
  }
  if (!operator) {
    return <Navigate to="/login" replace state={{ from: location }} />;
  }
  return <>{children}</>;
}
