import { Radio } from 'lucide-react';
import { useAsyncData } from '@/hooks/useAsyncData.js';
import { useSystemClock } from '@/hooks/useSystemClock.js';
import { fetchCommandCenterData } from '@/services/api/dashboardService.js';
import StatCard from '@/components/common/StatCard.jsx';
import Skeleton from '@/components/common/Skeleton.jsx';
import ErrorState from '@/components/common/ErrorState.jsx';
import PageHeader from '@/components/common/PageHeader.jsx';
import CrimeTrendChart from '@/components/dashboard/CrimeTrendChart.jsx';
import ActivityLogFeed from '@/components/dashboard/ActivityLogFeed.jsx';
import CommandActionsPanel from '@/components/dashboard/CommandActionsPanel.jsx';
import GeospatialHeatmapPreview from '@/components/dashboard/GeospatialHeatmapPreview.jsx';
export default function DashboardPage() {
  const { data, isLoading, error, refetch } = useAsyncData(fetchCommandCenterData, []);
  const sysTime = useSystemClock();

  return (
    <div className="p-8 max-w-[1400px] mx-auto flex flex-col gap-6">
      <PageHeader
        eyebrow="Global Overview • Active Operations"
        title="Command Center"
        actions={
          <div className="flex items-center gap-2 border border-border-subtle rounded-sm px-3 py-1.5">
            <Radio size={13} className="text-status-success" />
            <span className="font-mono text-xs text-ink-muted">SYS_TIME: {sysTime}</span>
          </div>
        }
      />

      {error && <ErrorState onRetry={refetch} message="Command Center data could not be loaded." />}

      {!error && (
        <>
          {/* KPI strip */}
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
            {isLoading || !data
              ? Array.from({ length: 4 }).map((_, i) => (
                  <div key={i} className="panel p-4">
                    <Skeleton className="h-3 w-20 mb-3" />
                    <Skeleton className="h-8 w-16" />
                  </div>
                ))
              : [
                  ['Total Crimes', data.summary.totalCrimes],
                  ['Active Cases', data.summary.activeCases],
                  ['High Risk Areas', data.summary.highRiskAreas],
                  ['Open FIRs', data.summary.openFirs],
                ].map(([label, stat]) => {
                  return (
                    <StatCard
                      key={label}
                      label={label}
                      value={stat.value.toLocaleString()}
                      trend={stat.trend}
                      trendTone={stat.trendTone}
                    />
                  );
                })}
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            <div className="lg:col-span-2 flex flex-col gap-6">
              <div className="panel p-4">
                <h3 className="font-display text-lg mb-2">Crime Trend Analysis</h3>
                {isLoading || !data ? (
                  <Skeleton className="h-44 w-full" />
                ) : (
                  <CrimeTrendChart data={data.crimeTrend} />
                )}
              </div>

              <div>
                <h3 className="font-display text-lg mb-2">Geospatial Heatmap</h3>
                {isLoading || !data ? (
                  <Skeleton className="h-56 w-full" />
                ) : (
                  <GeospatialHeatmapPreview hotspots={data.hotspots} />
                )}
              </div>
            </div>

            <div className="flex flex-col gap-6">
              {isLoading || !data ? (
                <Skeleton className="h-40 w-full panel" />
              ) : (
                <CommandActionsPanel actions={data.summary.commandActions || []} />
              )}

              {isLoading || !data ? (
                <div className="panel p-4">
                  <Skeleton rows={4} className="h-10 w-full" />
                </div>
              ) : (
                <ActivityLogFeed title="Recent Alerts" entries={data.alerts} />
              )}
            </div>
          </div>
        </>
      )}
    </div>
  );
}
