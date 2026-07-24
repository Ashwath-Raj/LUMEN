import { useState } from 'react';
import { useAsyncData } from '@/hooks/useAsyncData.js';
import { useSystemClock } from '@/hooks/useSystemClock.js';
import { fetchTacticalOverview } from '@/services/api/operationsService.js';
import PageHeader from '@/components/common/PageHeader.jsx';
import Skeleton from '@/components/common/Skeleton.jsx';
import ErrorState from '@/components/common/ErrorState.jsx';
import Badge from '@/components/common/Badge.jsx';
import MapPanel from '@/components/geospatial/MapPanel.jsx';
import ActivityLogFeed from '@/components/dashboard/ActivityLogFeed.jsx';
import IncidentQueueList from '@/components/operations/IncidentQueueList.jsx';
import ResourceMetricBar from '@/components/operations/ResourceMetricBar.jsx';

export default function TacticalDeploymentPage() {
  const { data, isLoading, error, refetch } = useAsyncData(fetchTacticalOverview, []);
  const [viewMode, setViewMode] = useState('tactical');
  const sysTime = useSystemClock();

  return (
    <div className="p-8 max-w-[1500px] mx-auto flex flex-col gap-6">
      <PageHeader
        eyebrow="Operations"
        title="Tactical Deployment Center"
        description="Real-time tactical overview and unit coordination matrix."
        actions={
          <div className="flex items-center gap-2">
            <Badge tone="warning">SEC-LVL: ALPHA</Badge>
            <Badge tone="success">LIVE {sysTime}</Badge>
          </div>
        }
      />

      {error && <ErrorState onRetry={refetch} message="Tactical overview could not be loaded." />}

      {!error && (
        <div className="grid grid-cols-1 lg:grid-cols-[340px_1fr] gap-6">
          <div className="flex flex-col gap-6">
            <div className="panel p-4">
              <h3 className="font-display text-lg mb-3">Incident Queue</h3>
              {isLoading || !data ? (
                <Skeleton rows={3} className="h-20 w-full" />
              ) : (
                <IncidentQueueList incidents={data.incidentQueue} />
              )}
            </div>

            <div className="panel p-4 flex flex-col gap-4">
              <h3 className="font-display text-lg">Resource Metrics</h3>
              {isLoading || !data ? (
                <Skeleton rows={2} className="h-14 w-full" />
              ) : (
                <>
                  <ResourceMetricBar
                    label="Field Operatives"
                    current={data.resourceMetrics.fieldOperatives.deployed}
                    total={data.resourceMetrics.fieldOperatives.total}
                    footnotes={[
                      `Deployed: ${data.resourceMetrics.fieldOperatives.deployedPct}%`,
                      `Reserves: ${data.resourceMetrics.fieldOperatives.reserves}`,
                    ]}
                  />
                  <ResourceMetricBar
                    label="Tactical Vehicles"
                    current={data.resourceMetrics.tacticalVehicles.active}
                    total={data.resourceMetrics.tacticalVehicles.total}
                    footnotes={[
                      `Active: ${data.resourceMetrics.tacticalVehicles.active}`,
                      `Maintenance: ${data.resourceMetrics.tacticalVehicles.maintenance}`,
                    ]}
                  />
                </>
              )}
            </div>
          </div>

          <div className="flex flex-col gap-6">
            <div className="h-[380px]">
              {isLoading || !data ? (
                <Skeleton className="h-full w-full" />
              ) : (
                <MapPanel viewMode={viewMode} onViewModeChange={setViewMode} hotspots={data.hotspots} />
              )}
            </div>

            {isLoading || !data ? (
              <Skeleton rows={4} className="h-10 w-full" />
            ) : (
              <ActivityLogFeed title="Coordination Log" entries={data.coordinationLog} />
            )}
          </div>
        </div>
      )}
    </div>
  );
}
