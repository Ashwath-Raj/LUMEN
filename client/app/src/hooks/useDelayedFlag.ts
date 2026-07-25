/**
 * `useDelayedFlag` — returns `true` only after `delayMs` of the input staying
 * true. Backs the §F rule "skeletons appear only after 300 ms to avoid flicker":
 * a fast response never flashes a skeleton. Resets immediately when the input
 * goes false.
 */
import { useEffect, useState } from "react";

export function useDelayedFlag(active: boolean, delayMs = 300): boolean {
  const [shown, setShown] = useState(false);

  useEffect(() => {
    if (!active) {
      setShown(false);
      return;
    }
    const id = window.setTimeout(() => setShown(true), delayMs);
    return () => window.clearTimeout(id);
  }, [active, delayMs]);

  return shown;
}
