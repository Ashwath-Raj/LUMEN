import { useParams } from 'react-router-dom';
import { History } from 'lucide-react';
import { useAsyncData } from '@/app/hooks/useAsyncData.js';
import { fetchCaseById } from '@/api/investigationService.js';
import PageHeader from '@/design/primitives/PageHeader.jsx';
import Skeleton from '@/design/primitives/Skeleton.jsx';
import ErrorState from '@/design/primitives/ErrorState.jsx';
import EmptyState from '@/design/primitives/EmptyState.jsx';
import TimelineNode from '@/components/timeline/TimelineNode.jsx';

export default function CaseTimelinePage() {
  const { caseId } = useParams();
  const { data, isLoading, error, refetch } = useAsyncData(() => fetchCaseById(caseId), [caseId]);

  return (
    <div className="p-8 max-w-[1400px] mx-auto flex flex-col gap-6">
      <PageHeader eyebrow={`Investigation / ${caseId}`} title="Timeline" />

      {error && <ErrorState onRetry={refetch} message="Timeline could not be loaded." />}

      {!error &&
        (isLoading || !data ? (
          <Skeleton rows={3} className="h-16 w-full" />
        ) : data.timeline.length === 0 ? (
          <EmptyState icon={History} title="No timeline events recorded" />
        ) : (
          <div className="panel p-5 flex flex-col gap-4">
            {data.timeline.map((event) => (
              <TimelineNode
                key={event.id}
                timestamp={event.timestamp}
                title={event.title}
                description={event.description}
              />
            ))}
          </div>
        ))}
    </div>
  );
}
