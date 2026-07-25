/**
 * `DelayedSkeleton` — a `Skeleton` that only appears after 300 ms (§F), so a fast
 * response never flashes a loader. Renders one or more skeleton lines sized for
 * the region. Until the delay elapses it renders nothing (reserving space is the
 * caller's job via container sizing).
 */
import { Skeleton } from "@/design/primitives";
import { useDelayedFlag } from "@/hooks/useDelayedFlag";
import { cn } from "@/utils/cn";

interface DelayedSkeletonProps {
  /** True while loading. The skeleton shows only after the delay. */
  loading: boolean;
  /** Number of stacked skeleton lines. */
  lines?: number;
  className?: string;
}

export function DelayedSkeleton({
  loading,
  lines = 3,
  className,
}: DelayedSkeletonProps) {
  const show = useDelayedFlag(loading);
  if (!show) return null;
  return (
    <div
      className={cn("flex flex-col gap-2", className)}
      role="status"
      aria-label="Loading"
      aria-busy="true"
    >
      {Array.from({ length: lines }).map((_, i) => (
        <Skeleton key={i} className={cn("h-4", i === lines - 1 && "w-2/3")} />
      ))}
    </div>
  );
}
