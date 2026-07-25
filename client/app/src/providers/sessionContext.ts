/**
 * Session context object + `useSession` hook, kept separate from the provider
 * component so the provider module stays component-only (React Fast Refresh
 * requires a file to export components exclusively). See SessionProvider.tsx.
 */
import { createContext, useContext } from "react";

import type { Operator, Session } from "@/types/session";

export interface SessionContextValue extends Session {
  loading: boolean;
  login: () => Promise<Operator | null>;
  logout: () => void;
}

export const SessionContext = createContext<SessionContextValue | null>(null);

export function useSession(): SessionContextValue {
  const ctx = useContext(SessionContext);
  if (!ctx) throw new Error("useSession must be used within a SessionProvider");
  return ctx;
}
