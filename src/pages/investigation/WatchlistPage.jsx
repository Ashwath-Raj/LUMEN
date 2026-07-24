import { Eye } from 'lucide-react';
import { useAsyncData } from '@/hooks/useAsyncData.js';
import { fetchWatchlist } from '@/services/api/investigationService.js';
import PageHeader from '@/components/common/PageHeader.jsx';
import Skeleton from '@/components/common/Skeleton.jsx';
import ErrorState from '@/components/common/ErrorState.jsx';
import EmptyState from '@/components/common/EmptyState.jsx';
import Badge from '@/components/common/Badge.jsx';

const RISK_TONE = { CRITICAL: 'critical', ELEVATED: 'warning', MODERATE: 'info' };

export default function WatchlistPage() {
  const { data, isLoading, error, refetch } = useAsyncData(fetchWatchlist, []);

  return (
    <div className="p-8 max-w-[1400px] mx-auto flex flex-col gap-6">
      <PageHeader
        eyebrow="Investigation"
        title="Watchlist"
        description="Individuals flagged for continued monitoring pending further evidence or identification."
      />

      {error && <ErrorState onRetry={refetch} message="Watchlist could not be loaded." />}

      {!error &&
        (isLoading || !data ? (
          <Skeleton rows={3} className="h-20 w-full" />
        ) : data.length === 0 ? (
          <EmptyState icon={Eye} title="Watchlist is empty" message="Flagged entities will appear here." />
        ) : (
          <ul className="flex flex-col gap-3">
            {data.map((entry) => (
              <li key={entry.id} className="panel p-4 flex items-start justify-between gap-4">
                <div>
                  <p className="label-eyebrow">{entry.id}</p>
                  <p className="font-display text-lg mt-0.5">{entry.name}</p>
                  <p className="text-ink-muted text-sm mt-1 max-w-xl">{entry.reason}</p>
                  <p className="text-xs text-ink-muted mt-1">Last seen: {entry.lastSeen}</p>
                </div>
                <Badge tone={RISK_TONE[entry.riskLevel] ?? 'neutral'}>{entry.riskLevel}</Badge>
              </li>
            ))}
          </ul>
        ))}
    </div>
  );
}
