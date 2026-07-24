import { Link } from 'react-router-dom';
import { Maximize2 } from 'lucide-react';

const INTENSITY_COLOR = {
  critical: 'bg-status-critical',
  high: 'bg-status-warning',
  moderate: 'bg-accent-gold',
};

/**
 * Small "Geospatial Heatmap" preview on the Command Center — a scaled-down,
 * non-interactive read of the full Geospatial module's hotspot map, with a
 * "Click to enlarge" affordance that deep-links there.
 */
export default function GeospatialHeatmapPreview({ hotspots = [] }) {
  return (
    <Link
      to="/geospatial"
      className="relative block h-56 rounded-sm border border-border-subtle bg-surface-2 overflow-hidden group"
    >
      <div className="absolute inset-0 bg-[radial-gradient(circle_at_30%_70%,rgba(201,162,39,0.08),transparent_60%)]" />
      {hotspots.map((spot) => (
        <span
          key={spot.id}
          style={{ left: `${spot.x}%`, top: `${spot.y}%` }}
          className={`absolute w-3 h-3 -translate-x-1/2 -translate-y-1/2 rounded-full ${INTENSITY_COLOR[spot.intensity] ?? 'bg-accent-gold'} opacity-80`}
        />
      ))}
      <div className="absolute bottom-2 right-2 flex items-center gap-1 text-[11px] text-ink-muted bg-surface-1/80 px-2 py-1 rounded-sm opacity-0 group-hover:opacity-100 transition-opacity">
        <Maximize2 size={12} />
        Click to enlarge
      </div>
    </Link>
  );
}
