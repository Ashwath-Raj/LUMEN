import { RadioTower } from 'lucide-react';
import { useAsyncData } from '@/hooks/useAsyncData.js';
import { fetchSignalIntercepts } from '@/services/api/analyticsService.js';
import PageHeader from '@/components/common/PageHeader.jsx';
import Skeleton from '@/components/common/Skeleton.jsx';
import ErrorState from '@/components/common/ErrorState.jsx';
import EmptyState from '@/components/common/EmptyState.jsx';
import Badge from '@/components/common/Badge.jsx';

export default function SignalIntelligencePage() {
  const { data, isLoading, error, refetch } = useAsyncData(fetchSignalIntercepts, []);

  return (
    <div className="p-8 max-w-[1400px] mx-auto flex flex-col gap-6">
      <PageHeader
        eyebrow="Analytics"
        title="Signal Intelligence"
        description="Intercepted communications and device signals correlated against active investigations."
      />

      {error && <ErrorState onRetry={refetch} message="Signal intercepts could not be loaded." />}

      {!error &&
        (isLoading || !data ? (
          <div className="flex flex-col gap-3">
            {Array.from({ length: 3 }).map((_, i) => (
              <Skeleton key={i} className="h-24 w-full" />
            ))}
          </div>
        ) : data.length === 0 ? (
          <EmptyState icon={RadioTower} title="No intercepts logged" message="Signal intelligence entries will appear here." />
        ) : (
          <ul className="flex flex-col gap-3">
            {data.map((sig) => (
              <li key={sig.id} className="panel p-4 flex items-start gap-4">
                <div className="w-10 h-10 rounded-sm bg-surface-2 flex items-center justify-center shrink-0">
                  <RadioTower size={18} className="text-accent-gold" strokeWidth={1.5} />
                </div>
                <div className="flex-1 min-w-0">
                  <div className="flex items-center justify-between flex-wrap gap-2">
                    <p className="label-eyebrow">{sig.id}</p>
                    <Badge tone={sig.tone}>{sig.confidence}% confidence</Badge>
                  </div>
                  <p className="text-ink-primary text-sm mt-1">{sig.source}</p>
                  <p className="text-ink-muted text-xs mt-0.5">{sig.summary}</p>
                  <div className="flex items-center gap-4 mt-2 text-xs text-ink-muted font-mono">
                    <span>{sig.timestamp}</span>
                    {sig.frequency !== 'N/A' && <span>{sig.frequency}</span>}
                    <span>Linked: {sig.linkedCase}</span>
                  </div>
                </div>
              </li>
            ))}
          </ul>
        ))}
    </div>
  );
}
