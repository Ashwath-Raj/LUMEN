/**
 * TanStack Query provider — the only server-state mechanism (arch §G).
 * One client for the app; per-endpoint caching/staleness lives in the hooks.
 */
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { useState, type ReactNode } from "react";

import { ApiError } from "@/api/client";

export function QueryProvider({ children }: { children: ReactNode }) {
  const [client] = useState(
    () =>
      new QueryClient({
        defaultOptions: {
          queries: {
            staleTime: 30_000,
            refetchOnWindowFocus: false,
            // Don't retry governance/validation denials — only genuinely
            // transient failures (arch §E error mapping; §29.3 retryable flag).
            retry: (failureCount, error) => {
              if (error instanceof ApiError) return error.retryable && failureCount < 2;
              return failureCount < 2;
            },
          },
        },
      }),
  );

  return <QueryClientProvider client={client}>{children}</QueryClientProvider>;
}
