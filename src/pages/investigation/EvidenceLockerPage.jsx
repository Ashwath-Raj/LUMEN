import { useState } from 'react';
import { Archive } from 'lucide-react';
import { useAsyncData } from '@/hooks/useAsyncData.js';
import { fetchEvidenceLocker } from '@/services/api/investigationService.js';
import PageHeader from '@/components/common/PageHeader.jsx';
import Skeleton from '@/components/common/Skeleton.jsx';
import ErrorState from '@/components/common/ErrorState.jsx';
import EmptyState from '@/components/common/EmptyState.jsx';
import EvidenceCard from '@/components/investigation/EvidenceCard.jsx';

export default function EvidenceLockerPage() {
  const { data, isLoading, error, refetch } = useAsyncData(fetchEvidenceLocker, []);
  const [selectedId, setSelectedId] = useState(null);

  return (
    <div className="p-8 max-w-[1400px] mx-auto flex flex-col gap-6">
      <PageHeader
        eyebrow="Investigation"
        title="Evidence Locker"
        description="Cross-case evidence catalog with chain-of-custody reference."
      />

      {error && <ErrorState onRetry={refetch} message="Evidence locker could not be loaded." />}

      {!error &&
        (isLoading || !data ? (
          <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-4 gap-4">
            {Array.from({ length: 8 }).map((_, i) => (
              <Skeleton key={i} className="h-40 w-full" />
            ))}
          </div>
        ) : data.length === 0 ? (
          <EmptyState icon={Archive} title="Evidence locker is empty" />
        ) : (
          <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-4 gap-4">
            {data.map((item) => (
              <EvidenceCard
                key={item.itemId}
                {...item}
                isSelected={selectedId === item.itemId}
                onClick={() => setSelectedId(item.itemId)}
              />
            ))}
          </div>
        ))}
    </div>
  );
}
