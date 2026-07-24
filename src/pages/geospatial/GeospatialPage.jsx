import { useEffect, useState } from 'react';
import { Moon, Sun, RefreshCw } from 'lucide-react';
import { useAsyncData } from '@/hooks/useAsyncData.js';
import { fetchGeospatialData, applyGeoParameters } from '@/services/api/geospatialService.js';
import PageHeader from '@/components/common/PageHeader.jsx';
import Skeleton from '@/components/common/Skeleton.jsx';
import ErrorState from '@/components/common/ErrorState.jsx';
import Checkbox from '@/components/common/Checkbox.jsx';
import Select from '@/components/common/Select.jsx';
import Button from '@/components/common/Button.jsx';
import MapPanel from '@/components/geospatial/MapPanel.jsx';
import PriorityHotspotsList from '@/components/geospatial/PriorityHotspotsList.jsx';
import SectorIntelCard from '@/components/geospatial/SectorIntelCard.jsx';

export default function GeospatialPage() {
  const { data, isLoading, error, refetch } = useAsyncData(fetchGeospatialData, []);

  const [timeOfDay, setTimeOfDay] = useState('night');
  const [timeValue, setTimeValue] = useState(50);
  const [layers, setLayers] = useState({});
  const [district, setDistrict] = useState('');
  const [incidentType, setIncidentType] = useState('');
  const [radius, setRadius] = useState('5.0');
  const [viewMode, setViewMode] = useState('tactical');
  const [selectedHotspotId, setSelectedHotspotId] = useState(null);
  const [isApplying, setIsApplying] = useState(false);
  const [appliedAt, setAppliedAt] = useState(null);

  // Seed controlled filter state once real data arrives (parameters come from the backend).
  useEffect(() => {
    if (!data) return;
    setDistrict((prev) => prev || data.parameters.districts[0] || '');
    setIncidentType((prev) => prev || data.parameters.incidentTypes[0] || '');
    setLayers((prev) =>
      Object.keys(prev).length > 0
        ? prev
        : Object.fromEntries(data.parameters.overlayLayers.map((l) => [l.id, l.defaultChecked]))
    );
  }, [data]);

  const selectedHotspot =
    data?.hotspots.find((h) => h.id === selectedHotspotId) ?? data?.hotspots[0] ?? null;

  const handleApply = async () => {
    setIsApplying(true);
    try {
      await applyGeoParameters({ district, incidentType, radius, timeOfDay, layers });
      setAppliedAt(new Date());
    } finally {
      setIsApplying(false);
    }
  };

  return (
    <div className="p-8 max-w-[1600px] mx-auto flex flex-col gap-6">
      <PageHeader
        eyebrow={`Geospatial • Active Session: ${data?.parameters.activeSession ?? '—'}`}
        title="Geospatial Intelligence"
        description="Layered crime density, risk zones, and live hotspot correlation across the district."
      />

      {error && <ErrorState onRetry={refetch} message="Geospatial data could not be loaded." />}

      {!error && (
        <div className="grid grid-cols-1 lg:grid-cols-[280px_1fr_300px] gap-6 items-start">
          {/* Geographic Parameters */}
          <div className="panel p-4 flex flex-col gap-5">
            <h2 className="font-display text-lg">Geographic Parameters</h2>

            <div>
              <p className="label-eyebrow mb-2">Time of Day</p>
              <input
                type="range"
                min={0}
                max={100}
                value={timeValue}
                onChange={(e) => setTimeValue(Number(e.target.value))}
                className="w-full accent-accent-gold"
                aria-label="Time of day"
              />
              <div className="flex justify-between text-[10px] font-mono text-ink-muted mt-1">
                <span>00:00</span>
                <span>12:00</span>
                <span>23:59</span>
              </div>
              <div className="flex gap-2 mt-3">
                <button
                  type="button"
                  onClick={() => setTimeOfDay('night')}
                  className={`flex-1 flex items-center justify-center gap-1.5 text-xs py-1.5 rounded-sm border transition-colors ${
                    timeOfDay === 'night'
                      ? 'border-accent-gold text-accent-gold'
                      : 'border-border-subtle text-ink-muted'
                  }`}
                >
                  <Moon size={13} /> Night
                </button>
                <button
                  type="button"
                  onClick={() => setTimeOfDay('day')}
                  className={`flex-1 flex items-center justify-center gap-1.5 text-xs py-1.5 rounded-sm border transition-colors ${
                    timeOfDay === 'day'
                      ? 'border-accent-gold text-accent-gold'
                      : 'border-border-subtle text-ink-muted'
                  }`}
                >
                  <Sun size={13} /> Day
                </button>
              </div>
            </div>

            <div>
              <p className="label-eyebrow mb-2">Overlay Layers</p>
              <div className="flex flex-col gap-2.5">
                {isLoading || !data
                  ? <Skeleton rows={4} className="h-4 w-full" />
                  : data.parameters.overlayLayers.map((layer) => (
                      <Checkbox
                        key={layer.id}
                        id={layer.id}
                        label={layer.label}
                        checked={Boolean(layers[layer.id])}
                        onChange={(checked) => setLayers((prev) => ({ ...prev, [layer.id]: checked }))}
                      />
                    ))}
              </div>
            </div>

            <div className="flex flex-col gap-3">
              <p className="label-eyebrow -mb-1">Filter Criteria</p>
              {isLoading || !data ? (
                <Skeleton rows={2} className="h-9 w-full" />
              ) : (
                <>
                  <Select
                    id="district"
                    label="District"
                    value={district}
                    onChange={setDistrict}
                    options={data.parameters.districts}
                  />
                  <Select
                    id="incidentType"
                    label="Incident Type"
                    value={incidentType}
                    onChange={setIncidentType}
                    options={data.parameters.incidentTypes}
                  />
                  <div className="flex flex-col gap-1.5">
                    <label htmlFor="radius" className="label-eyebrow">
                      Radius (km)
                    </label>
                    <input
                      id="radius"
                      type="number"
                      step="0.5"
                      min="0"
                      value={radius}
                      onChange={(e) => setRadius(e.target.value)}
                      className="bg-surface-2 border border-border-subtle rounded-sm px-3 py-2 text-sm text-ink-primary focus:border-accent-gold outline-none transition-colors"
                    />
                  </div>
                </>
              )}
            </div>

            <Button
              onClick={handleApply}
              disabled={isLoading || isApplying}
              className="flex items-center justify-center gap-2"
            >
              <RefreshCw size={14} className={isApplying ? 'animate-spin' : ''} />
              {isApplying ? 'Applying...' : 'Apply Parameters'}
            </Button>
            {appliedAt && (
              <p className="text-xs text-status-success text-center -mt-2">
                Applied at {appliedAt.toLocaleTimeString()}
              </p>
            )}
          </div>

          {/* Map */}
          <div className="h-[560px]">
            {isLoading || !data ? (
              <Skeleton className="h-full w-full" />
            ) : (
              <MapPanel
                viewMode={viewMode}
                onViewModeChange={setViewMode}
                hotspots={data.hotspots}
                selectedId={selectedHotspot?.id}
                onSelectHotspot={setSelectedHotspotId}
              />
            )}
          </div>

          {/* Priority Hotspots + Sector Intel */}
          <div className="flex flex-col gap-6">
            {isLoading || !data ? (
              <Skeleton rows={3} className="h-16 w-full" />
            ) : (
              <PriorityHotspotsList
                hotspots={data.hotspots}
                selectedId={selectedHotspot?.id}
                onSelect={setSelectedHotspotId}
              />
            )}

            {isLoading || !data ? (
              <Skeleton className="h-32 w-full" />
            ) : (
              <SectorIntelCard {...data.sectorIntel} />
            )}
          </div>
        </div>
      )}
    </div>
  );
}
