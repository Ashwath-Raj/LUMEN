/**
 * `Skeleton` — a neutral loading placeholder. Per §F, skeletons appear only
 * after a 300 ms delay (--motion-skeleton-delay) to avoid flicker; the delay is
 * applied by the consumer that shows it, not baked into the shape.
 */
import { cn } from "@/utils/cn";

export function Skeleton({ className }: { className?: string }) {
  return (
    <div
      aria-hidden
      className={cn("animate-pulse rounded bg-raised", className)}
    />
  );
}
