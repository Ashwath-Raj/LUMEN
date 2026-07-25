/**
 * Session context — arch §G ("one small session context: user, role, scope,
 * degradation level from the last envelope"). This is the ONLY client state
 * besides the URL; there is no global store.
 *
 * Holds the authenticated operator (via authService), and tracks the latest
 * degradation level published by the envelope client (api/client.onDegradation)
 * so the shell's `DegradationPill` reacts without every component wiring it.
 *
 * Role and scopeLabel come from the backend's policy scoping (spec §20); Session
 * 0 exposes the fields and leaves them null until the login/session sessions
 * populate them from a real endpoint — Cannot determine from specification for
 * a role-lookup endpoint shape, so none is invented here.
 *
 * The context object and `useSession` hook live in sessionContext.ts so this
 * module exports only the provider component (Fast Refresh requirement).
 */
import { useEffect, useMemo, useState, type ReactNode } from "react";

import { onDegradation } from "@/api/client";
import * as authService from "@/api/authService";
import type { DegradationLevel } from "@/types/envelope";
import type { Operator, Role } from "@/types/session";
import { SessionContext, type SessionContextValue } from "./sessionContext";

export function SessionProvider({ children }: { children: ReactNode }) {
  const [operator, setOperator] = useState<Operator | null>(null);
  const [role] = useState<Role | null>(null);
  const [scopeLabel] = useState<string | null>(null);
  const [degradationLevel, setDegradationLevel] =
    useState<DegradationLevel>("L0");
  const [loading, setLoading] = useState(true);

  // Resolve the current operator once on mount.
  useEffect(() => {
    let active = true;
    authService
      .fetchCurrentOperator()
      .then((op) => {
        if (active) setOperator(op);
      })
      .finally(() => {
        if (active) setLoading(false);
      });
    return () => {
      active = false;
    };
  }, []);

  // Track degradation level from every envelope (arch §G / §E).
  useEffect(() => onDegradation(setDegradationLevel), []);

  const value = useMemo<SessionContextValue>(
    () => ({
      operator,
      role,
      scopeLabel,
      degradationLevel,
      loading,
      login: async () => {
        const op = await authService.login();
        if (op) setOperator(op);
        return op;
      },
      logout: () => {
        authService.logout();
        setOperator(null);
      },
    }),
    [operator, role, scopeLabel, degradationLevel, loading],
  );

  return (
    <SessionContext.Provider value={value}>{children}</SessionContext.Provider>
  );
}
