import { Radio } from 'lucide-react';

const PROBABILITY_TONE = (p) => {
  if (p >= 90) return 'text-status-critical';
  if (p >= 70) return 'text-status-warning';
  return 'text-accent-gold';
};

/**
 * "Priority Hotspots" panel — ranked list of geospatial hotspots with
 * probability score and incident count, LIVE-tagged per the Figma.
 */
export default function PriorityHotspotsList({ hotspots = [], selectedId, onSelect }) {
  return (
    <div className="panel p-4">
      <div className="flex items-center justify-between mb-3">
        <h3 className="font-display text-lg">Priority Hotspots</h3>
        <span className="flex items-center gap-1 text-xs text-status-critical">
          <Radio size={12} />
          LIVE
        </span>
      </div>
      <ul className="flex flex-col divide-y divide-border-subtle">
        {hotspots.map((spot) => (
          <li key={spot.id}>
            <button
              type="button"
              onClick={() => onSelect?.(spot.id)}
              className={`w-full text-left py-2.5 transition-colors ${
                selectedId === spot.id ? 'text-accent-gold' : ''
              }`}
            >
              <div className="flex items-center justify-between">
                <span className="label-eyebrow">{spot.id}</span>
                <span className={`text-xs font-mono ${PROBABILITY_TONE(spot.probability)}`}>
                  {spot.probability}% PROBABILITY
                </span>
              </div>
              <p className="text-sm text-ink-primary mt-0.5">{spot.label}</p>
              <p className="text-xs text-ink-muted mt-0.5">
                {spot.incidents} Incidents / {spot.windowHours}h
              </p>
            </button>
          </li>
        ))}
      </ul>
    </div>
  );
}
