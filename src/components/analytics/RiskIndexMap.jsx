const scoreTone = (score) => {
  if (score >= 75) return { bar: 'bg-status-critical', text: 'text-status-critical' };
  if (score >= 50) return { bar: 'bg-status-warning', text: 'text-status-warning' };
  return { bar: 'bg-status-success', text: 'text-status-success' };
};

/**
 * "Risk Index Map" panel on Crime Statistics & Pattern Analysis. A ranked
 * bar-list rather than a literal map — keeps this screen distinct from the
 * Geospatial module's actual MapPanel while still visualizing the same
 * kind of sector risk data.
 */
export default function RiskIndexMap({ areas = [] }) {
  return (
    <ul className="flex flex-col gap-3">
      {areas.map((area) => {
        const tone = scoreTone(area.score);
        return (
          <li key={area.id}>
            <div className="flex items-center justify-between text-sm mb-1">
              <span className="text-ink-secondary">{area.label}</span>
              <span className={`font-mono text-xs ${tone.text}`}>{area.score}</span>
            </div>
            <div className="h-1.5 rounded-full bg-surface-2 overflow-hidden">
              <div className={`h-full ${tone.bar}`} style={{ width: `${area.score}%` }} />
            </div>
          </li>
        );
      })}
    </ul>
  );
}
