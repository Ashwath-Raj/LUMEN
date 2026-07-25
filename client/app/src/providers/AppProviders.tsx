/**
 * Root provider composition (arch §G). One place wraps the app in server-state
 * (Query) and session context, in the correct order. `main.tsx` renders this
 * around the router.
 */
import type { ReactNode } from "react";

import { QueryProvider } from "./QueryProvider";
import { SessionProvider } from "./SessionProvider";

export function AppProviders({ children }: { children: ReactNode }) {
  return (
    <QueryProvider>
      <SessionProvider>{children}</SessionProvider>
    </QueryProvider>
  );
}
