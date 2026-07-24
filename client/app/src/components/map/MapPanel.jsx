import { useState, useRef } from 'react';
import { ZoomIn, ZoomOut, LocateFixed, Layers } from 'lucide-react';

const INTENSITY_COLOR = {
  critical: 'bg-status-critical',
  high: 'bg-status-warning',
  moderate: 'bg-accent-gold',
};

/**
 * Shared map surface for Geospatial Intelligence and the Operations
 * "Theatre Map". `viewMode` toggles TACTICAL VIEW / INFRARED per the
 * Figma legend (Priority Target / Friendly Unit markers). Renders
 * `hotspots` as positioned markers with a pulsing ring on the selected one.
 */
export default function MapPanel({
  viewMode = 'tactical',
  onViewModeChange,
  hotspots = [],
  selectedId,
  onSelectHotspot,
  children,
}) {
  const [pan, setPan] = useState({ x: 0, y: 0 });
  const [zoom, setZoom] = useState(1);
  const [isDragging, setIsDragging] = useState(false);
  const containerRef = useRef(null);

  const handlePointerDown = (e) => {
    if (e.button !== 0 || e.target.closest('button')) return; // Ignore if clicking a button
    e.currentTarget.setPointerCapture(e.pointerId);
    setIsDragging(true);
  };

  const handlePointerMove = (e) => {
    if (!isDragging) return;
    setPan(prev => ({
      x: prev.x + e.movementX,
      y: prev.y + e.movementY
    }));
  };

  const handlePointerUp = (e) => {
    if (isDragging) {
      e.currentTarget.releasePointerCapture(e.pointerId);
      setIsDragging(false);
    }
  };

  const resetView = () => {
    setPan({ x: 0, y: 0 });
    setZoom(1);
  };

  const handleZoomIn = () => setZoom(prev => Math.min(prev + 0.25, 3));
  const handleZoomOut = () => setZoom(prev => Math.max(prev - 0.25, 0.5));

  return (
    <div 
      className={`panel relative w-full h-full min-h-[420px] overflow-hidden bg-surface-2 select-none ${isDragging ? 'cursor-grabbing' : 'cursor-grab'}`}
      ref={containerRef}
      onPointerDown={handlePointerDown}
      onPointerMove={handlePointerMove}
      onPointerUp={handlePointerUp}
      onPointerLeave={handlePointerUp}
      style={{ touchAction: 'none' }}
    >
      {/* Background gradient moves with pan slightly for parallax effect, or stays static. Static is easier. */}
      <div
        className={`absolute inset-0 transition-colors pointer-events-none ${
          viewMode === 'infrared'
            ? 'bg-[radial-gradient(circle_at_50%_50%,rgba(192,57,43,0.18),transparent_70%)]'
            : 'bg-[radial-gradient(circle_at_30%_30%,rgba(201,162,39,0.08),transparent_60%)]'
        }`}
      />

      {/* Top Left Controls */}
      <div className="absolute top-3 left-3 flex gap-2 z-20">
        <button
          type="button"
          onClick={() => onViewModeChange?.('tactical')}
          className={`text-xs font-mono px-2 py-1 rounded-sm transition-colors cursor-default ${viewMode === 'tactical' ? 'bg-surface-3 text-ink-primary' : 'bg-surface-1 text-ink-muted'}`}
        >
          TACTICAL VIEW
        </button>
        <button
          type="button"
          onClick={() => onViewModeChange?.('infrared')}
          className={`text-xs font-mono px-2 py-1 rounded-sm transition-colors cursor-default ${viewMode === 'infrared' ? 'bg-surface-3 text-ink-primary' : 'bg-surface-1 text-ink-muted'}`}
        >
          INFRARED
        </button>
      </div>

      {/* Bottom Right Controls */}
      <div className="absolute bottom-3 right-3 flex flex-col gap-1.5 z-20">
        <button
          type="button"
          onClick={handleZoomIn}
          aria-label="Zoom in"
          className="w-8 h-8 rounded-sm bg-surface-1 border border-border-subtle flex items-center justify-center text-ink-secondary hover:text-accent-gold hover:border-accent-gold transition-colors"
        >
          <ZoomIn size={14} />
        </button>
        <button
          type="button"
          onClick={handleZoomOut}
          aria-label="Zoom out"
          className="w-8 h-8 rounded-sm bg-surface-1 border border-border-subtle flex items-center justify-center text-ink-secondary hover:text-accent-gold hover:border-accent-gold transition-colors"
        >
          <ZoomOut size={14} />
        </button>
        <button
          type="button"
          onClick={resetView}
          aria-label="Reset view"
          className="w-8 h-8 rounded-sm bg-surface-1 border border-border-subtle flex items-center justify-center text-ink-secondary hover:text-accent-gold hover:border-accent-gold transition-colors"
        >
          <LocateFixed size={14} />
        </button>
        <button
          type="button"
          aria-label="Layers"
          className="w-8 h-8 rounded-sm bg-surface-1 border border-border-subtle flex items-center justify-center text-ink-secondary hover:text-accent-gold hover:border-accent-gold transition-colors"
        >
          <Layers size={14} />
        </button>
      </div>

      {/* Panning/Zooming Surface */}
      <div 
        className="absolute inset-0 pointer-events-none transition-transform duration-75 origin-center"
        style={{ transform: `translate(${pan.x}px, ${pan.y}px) scale(${zoom})` }}
      >
        {hotspots.map((spot) => (
          <button
            key={spot.id}
            type="button"
            onClick={(e) => { e.stopPropagation(); onSelectHotspot?.(spot.id); }}
            style={{ left: `${spot.x}%`, top: `${spot.y}%` }}
            className="absolute -translate-x-1/2 -translate-y-1/2 z-10 group pointer-events-auto cursor-default"
            aria-label={spot.label}
          >
            {selectedId === spot.id && (
              <span
                className={`absolute inset-0 -m-2 rounded-full ${INTENSITY_COLOR[spot.intensity] ?? 'bg-accent-gold'} opacity-30 animate-ping`}
              />
            )}
            <span
              className={`relative block w-3.5 h-3.5 rounded-full border-2 border-surface-0 ${INTENSITY_COLOR[spot.intensity] ?? 'bg-accent-gold'}`}
            />
            <span className="absolute left-1/2 -translate-x-1/2 top-full mt-1 whitespace-nowrap text-[10px] font-mono text-ink-secondary bg-surface-1/90 px-1.5 py-0.5 rounded-sm opacity-0 group-hover:opacity-100 transition-opacity">
              {spot.label}
            </span>
          </button>
        ))}

        <div className="pointer-events-auto">
          {children}
        </div>
      </div>
    </div>
  );
}
