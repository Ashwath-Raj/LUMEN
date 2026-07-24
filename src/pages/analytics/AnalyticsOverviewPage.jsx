import { useAsyncData } from '@/hooks/useAsyncData.js';
import { fetchCrimeStatistics } from '@/services/api/analyticsService.js';
import PageHeader from '@/components/common/PageHeader.jsx';
import StatCard from '@/components/common/StatCard.jsx';
import Skeleton from '@/components/common/Skeleton.jsx';
import ErrorState from '@/components/common/ErrorState.jsx';
import NetworkGraph from '@/components/investigation/NetworkGraph.jsx';
import RiskIndexMap from '@/components/analytics/RiskIndexMap.jsx';
import CategoryBreakdownList from '@/components/analytics/CategoryBreakdownList.jsx';
import ActivityLogFeed from '@/components/dashboard/ActivityLogFeed.jsx';

export default function AnalyticsOverviewPage() {
  const { data, isLoading, error, refetch } = useAsyncData(fetchCrimeStatistics, []);

  return (
    <div className="p-8 max-w-[1400px] mx-auto flex flex-col gap-6">
      <PageHeader
        eyebrow="Analytics"
        title="Crime Statistics & Pattern Analysis"
        description="Aggregated statistical overview, behavioral correlation, and category trends across active investigations."
      />

      {error && <ErrorState onRetry={refetch} message="Statistics could not be loaded." />}

      {!error && (
        <>
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
            {isLoading || !data
              ? Array.from({ length: 4 }).map((_, i) => (
                  <div key={i} className="panel p-4">
                    <Skeleton className="h-3 w-24 mb-3" />
                    <Skeleton className="h-8 w-16" />
                  </div>
                ))
              : data.overview.map((stat) => (
                  <StatCard
                    key={stat.id}
                    label={stat.label}
                    value={stat.value}
                    trend={stat.trend}
                    trendTone={stat.trendTone}
                  />
                ))}
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <div className="panel p-4">
              <h3 className="font-display text-lg mb-3">Behavioral Pattern Correlation</h3>
              {isLoading || !data ? (
                <Skeleton className="h-64 w-full" />
              ) : (
                <NetworkGraph nodes={data.behavioralNodes} edges={data.behavioralEdges} />
              )}
            </div>

            <div className="panel p-4">
              <h3 className="font-display text-lg mb-3">Risk Index Map</h3>
              {isLoading || !data ? (
                <Skeleton rows={6} className="h-5 w-full" />
              ) : (
                <RiskIndexMap areas={data.riskIndex} />
              )}
            </div>
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <div className="panel p-4">
              <h3 className="font-display text-lg mb-1">Category Analysis</h3>
              {isLoading || !data ? (
                <Skeleton rows={5} className="h-6 w-full" />
              ) : (
                <CategoryBreakdownList categories={data.categoryBreakdown} />
              )}
            </div>

            {isLoading || !data ? (
              <div className="panel p-4">
                <Skeleton rows={3} className="h-10 w-full" />
              </div>
            ) : (
              <ActivityLogFeed title="Recent Feed Injections" entries={data.recentFeedInjections} />
            )}
          </div>
        </>
      )}
    </div>
  );
}
