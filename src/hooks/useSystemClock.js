import { useEffect, useState } from 'react';

/** Ticks every second; returns a formatted UTC time string like "14:02:45Z". */
export function useSystemClock() {
  const [now, setNow] = useState(() => new Date());

  useEffect(() => {
    const id = setInterval(() => setNow(new Date()), 1000);
    return () => clearInterval(id);
  }, []);

  return `${now.toISOString().substring(11, 19)}Z`;
}
